# -*- coding: utf-8 -*-
"""
=================================================================
项目名称：校园外卖两段式配送数据库系统 (campus_delivery_db)
文件名称：generate_mock_data.py
功能描述：使用 Faker 库生成海量模拟数据用于答辩大屏展示
         包含 50用户 / 15商家(各5菜品) / 1000历史订单流水
适用环境：Python 3.8+ / pymysql / faker
=================================================================
"""

import random
import time
from datetime import datetime, timedelta
import os

import pymysql
from faker import Faker
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# ==================================================================
# 数据库连接配置 — 从 .env 文件读取，防止密码泄露
# ==================================================================
DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD"),
    "database": os.getenv("MYSQL_DATABASE", "campus_delivery_db"),
    "charset": os.getenv("MYSQL_CHARSET", "utf8mb4"),
    "cursorclass": pymysql.cursors.DictCursor,
}

fake = Faker("zh_CN")  # 本地化中文模拟数据


# ------------------------------------------------------------------
# 工具函数：连接数据库
# ------------------------------------------------------------------
def get_connection():
    return pymysql.connect(**DB_CONFIG)


# ------------------------------------------------------------------
# 步骤 0：清理旧数据（解决外键冲突，彻底清空）
# ------------------------------------------------------------------
def clean_old_data(conn):
    """清空所有涉及的表，避免外键冲突"""
    print("=" * 60)
    print("🧹 步骤 0：正在清理旧数据……")
    with conn.cursor() as cursor:
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        cursor.execute("TRUNCATE TABLE order_items")
        cursor.execute("TRUNCATE TABLE orders")
        cursor.execute("TRUNCATE TABLE dishes")
        cursor.execute("TRUNCATE TABLE merchants")
        cursor.execute("TRUNCATE TABLE users")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    conn.commit()
    print("✅ 旧数据已全部清空！")
    print("=" * 60)


# ------------------------------------------------------------------
# 步骤 1：生成学生数据 (50条)
# ------------------------------------------------------------------
def generate_users(conn, num=50):
    print(f"\n👤 步骤 1：正在生成 {num} 个学生用户……")
    sql = """INSERT INTO users (username, phone, dorm_building, room_number, balance)
             VALUES (%s, %s, %s, %s, %s)"""
    data = []
    for _ in range(num):
        username = fake.name()
        phone = fake.phone_number()
        # 限制手机号长度不超过20
        if len(phone) > 20:
            phone = phone[:20]
        building = f"{random.choice(['1期','2期','3期'])}{random.randint(1,15)}栋"
        room = f"{random.randint(1,6)}{random.choice(['A','B','C'])}{random.randint(1,30):02d}"
        balance = round(random.uniform(50, 500), 2)
        data.append((username, phone, building, room, balance))

    with conn.cursor() as cursor:
        cursor.executemany(sql, data)
    conn.commit()
    print(f"✅ 成功插入 {num} 个学生用户！")


# ------------------------------------------------------------------
# 步骤 2：生成商家数据 (15条)
# ------------------------------------------------------------------
def generate_merchants(conn, num=15):
    print(f"\n🏪 步骤 2：正在生成 {num} 个商家……")
    # 有真实感的店名词库
    prefix_list = ["好再来", "天天", "一品", "香满园", "味美滋",
                   "食尚", "舌尖", "小当家", "阿妈", "旺角",
                   "老街", "校园", "学子", "翰林", "状元"]
    suffix_list = ["麻辣烫", "黄焖鸡", "奶茶店", "饺子馆", "盖浇饭",
                   "米线店", "炸鸡店", "烘焙坊", "水果捞", "面馆",
                   "煲仔饭", "寿司店", "麻辣香锅", "烤鱼店", "煎饼果子"]
    sql = """INSERT INTO merchants (merchant_name, phone, address, rating)
             VALUES (%s, %s, %s, %s)"""
    data = []
    used_names = set()
    for _ in range(num):
        # 确保不重名
        while True:
            name = f"{random.choice(prefix_list)}{random.choice(suffix_list)}"
            if name not in used_names:
                used_names.add(name)
                break
        phone = f"1{random.choice(['38','39','55','77','88'])}{random.randint(10000000,99999999)}"[:15]
        addr = f"{random.choice(['丁香餐厅','玫瑰餐厅','紫荆餐厅','下沉广场','综合楼'])}{random.choice(['一楼','二楼','三楼','负一楼'])}{random.choice(['核心区','侧廊','尽头','入口处'])}"
        rating = round(random.uniform(3.5, 5.0), 1)
        data.append((name, phone, addr, rating))

    with conn.cursor() as cursor:
        cursor.executemany(sql, data)
    conn.commit()
    print(f"✅ 成功插入 {num} 个商家！")


# ------------------------------------------------------------------
# 步骤 3：生成菜品数据 (每个商家5道菜)
# ------------------------------------------------------------------
def generate_dishes(conn, dishes_per_merchant=5):
    print(f"\n🍽️ 步骤 3：正在为每个商家生成 {dishes_per_merchant} 道菜品……")
    dish_names = [
        "经典麻辣烫", "番茄牛腩面", "宫保鸡丁饭", "鱼香肉丝饭", "糖醋里脊饭",
        "酸菜鱼米线", "香辣鸡腿堡", "珍珠奶茶", "芒果冰沙", "鸡蛋灌饼",
        "牛肉拉面", "蛋炒饭", "葱油拌面", "小笼包(8只)", "煎饺(12只)",
        "烤冷面", "手抓饼", "皮蛋瘦肉粥", "豆浆油条套餐", "卤肉饭",
        "咖喱鸡肉饭", "黑椒牛柳意面", "芝士焗饭", "日式拉面", "韩式拌饭",
    ]

    with conn.cursor() as cursor:
        cursor.execute("SELECT merchant_id FROM merchants")
        merchant_ids = [row["merchant_id"] for row in cursor.fetchall()]

    sql = """INSERT INTO dishes (merchant_id, dish_name, price, stock, status)
             VALUES (%s, %s, %s, %s, %s)"""
    data = []
    idx = 0
    for mid in merchant_ids:
        for _ in range(dishes_per_merchant):
            name = dish_names[idx % len(dish_names)]
            idx += 1
            price = round(random.uniform(10, 30), 2)
            stock = 500  # 故意设置大库存避免频繁触发超卖
            status = 1
            data.append((mid, name, price, stock, status))

    with conn.cursor() as cursor:
        cursor.executemany(sql, data)
    conn.commit()
    total = len(data)
    print(f"✅ 成功插入 {total} 道菜品！")


# ------------------------------------------------------------------
# 步骤 4：生成订单流水 (1000条) + 明细
# ------------------------------------------------------------------
def generate_orders(conn, num_orders=1000):
    print(f"\n📦 步骤 4：正在生成 {num_orders} 条历史订单流水（含明细）……")

    with conn.cursor() as cursor:
        cursor.execute("SELECT user_id FROM users")
        user_ids = [row["user_id"] for row in cursor.fetchall()]

        cursor.execute("SELECT merchant_id FROM merchants")
        merchant_ids = [row["merchant_id"] for row in cursor.fetchall()]

        cursor.execute("SELECT point_id, point_name FROM pickup_points")
        points_data = cursor.fetchall()
        point_ids = [row["point_id"] for row in points_data]

        cursor.execute("SELECT dish_id, merchant_id, price FROM dishes")
        dishes_data = cursor.fetchall()

        cursor.execute("SELECT rider_id, rider_type FROM riders")
        riders_data = cursor.fetchall()

    # 找出"3期智能寄存柜"的 ID（用来制造爆仓危机）
    overload_point_id = None
    for p in points_data:
        if "3期" in p["point_name"]:
            overload_point_id = p["point_id"]
            break
    if overload_point_id is None:
        overload_point_id = point_ids[0]  # fallback

    # 拆分骑手
    trunk_riders = [r["rider_id"] for r in riders_data if r["rider_type"] == "Stage1_Trunk"]
    floor_riders = [r["rider_id"] for r in riders_data if r["rider_type"] == "Stage2_Floor"]

    # 按商家分组菜品
    dishes_by_merchant = {}
    for d in dishes_data:
        mid = d["merchant_id"]
        dishes_by_merchant.setdefault(mid, []).append(d)

    # 订单状态概率权重
    status_weights = [
        ("Paid", 5),
        ("Stage1_Assigned", 10),
        ("Arrived_At_Point", 15),
        ("Stage2_Assigned", 20),
        ("Completed", 50),  # 一半的订单都是完成的，便于展示数据
    ]
    status_list = [s for s, w in status_weights for _ in range(w)]

    # ===== 爆仓策略：强制塞满 3期智能寄存柜 =====
    # capacity=80, 需要 >64 个 Arrived_At_Point 才能超过 80%
    # 我们塞 68 个订单到 3期，状态全设为 Arrived_At_Point (68/80=85%)
    OVERLOAD_COUNT = 68
    overload_order_ids = []  # 记录这些订单的 order_id，方便后续追溯
    overload_done = 0
    print(f"\n   💥 爆仓策略：正在向 '3期智能寄存柜' 注入 {OVERLOAD_COUNT} 个滞留包裹……")

    order_insert_sql = """INSERT INTO orders
        (user_id, merchant_id, pickup_point_id, total_amount, order_status,
         stage1_rider_id, stage2_rider_id,
         created_at, stage1_completed_at, stage2_completed_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""

    item_insert_sql = """INSERT INTO order_items
        (order_id, dish_id, quantity, price_at_order)
        VALUES (%s, %s, %s, %s)"""

    now = datetime.now()

    with conn.cursor() as cursor:
        for order_index in range(num_orders):
            # ---- 随机选择基础关联 ----
            user_id = random.choice(user_ids)
            merchant_id = random.choice(merchant_ids)

            # ===== 爆仓策略：前 OVERLOAD_COUNT 条订单强制塞入 3期智能寄存柜 =====
            if order_index < OVERLOAD_COUNT:
                point_id = overload_point_id
                order_status = "Arrived_At_Point"
            else:
                point_id = random.choice(point_ids)
                order_status = random.choice(status_list)

            # ---- 构造时间线（下单时间在过去30天内） ----
            created_at = now - timedelta(
                days=random.randint(0, 30),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59),
                seconds=random.randint(0, 59),
            )

            stage1_completed_at = None
            stage2_completed_at = None

            # ---- 根据状态推进时间线 ----
            if order_status in ("Stage1_Assigned", "Arrived_At_Point", "Stage2_Assigned", "Completed"):
                stage1_completed_at = created_at + timedelta(minutes=random.randint(10, 40))

            if order_status in ("Stage2_Assigned", "Completed"):
                stage2_completed_at = stage1_completed_at + timedelta(minutes=random.randint(5, 25))

            if order_status == "Completed":
                # 确保完成时间一定在派送后
                stage2_completed_at = stage1_completed_at + timedelta(minutes=random.randint(5, 25))

            # ---- 拼装菜品明细 ----
            available_dishes = dishes_by_merchant.get(merchant_id, [])
            if not available_dishes:
                continue

            selected_dish = random.choice(available_dishes)
            quantity = random.randint(1, 3)
            price_at_order = float(selected_dish["price"])
            total_amount = round(price_at_order * quantity, 2)

            # ---- 骑手指派 ----
            stage1_rider = random.choice(trunk_riders) if trunk_riders else None
            stage2_rider = random.choice(floor_riders) if floor_riders else None

            # ---- 插入订单（单条插入确保拿到准确的 order_id） ----
            cursor.execute(order_insert_sql, (
                user_id, merchant_id, point_id, total_amount, order_status,
                stage1_rider, stage2_rider,
                created_at, stage1_completed_at, stage2_completed_at,
            ))
            order_id = cursor.lastrowid

            # ---- 插入明细 ----
            cursor.execute(item_insert_sql, (order_id, selected_dish["dish_id"], quantity, price_at_order))

            # ---- 每 50 条提交一次 + 打印进度 ----
            if (order_index + 1) % 50 == 0 or order_index == num_orders - 1:
                conn.commit()
                progress = order_index + 1
                print(f"   📊 进度: {progress}/{num_orders} 条订单已生成 ({progress*100/num_orders:.0f}%)")

    print(f"✅ 成功插入 {num_orders} 条订单及对应明细！")
    return overload_point_id


# ------------------------------------------------------------------
# 步骤 5：同步寄存点包裹计数（让大屏正确显示饱和度）
# ------------------------------------------------------------------
def sync_pickup_packages(conn, overload_point_id):
    """
    根据 orders 表中 Arrived_At_Point 状态的订单数，
    更新 pickup_points 表的 current_packages 字段。
    """
    print(f"\n[步骤 5] 正在同步寄存点包裹计数……")
    with conn.cursor() as cursor:
        # 先统计每个寄存点中有多少 Arrived_At_Point 状态的订单
        cursor.execute("""
            SELECT pp.point_id, pp.capacity, COUNT(o.pickup_point_id) AS cnt
            FROM pickup_points pp
            LEFT JOIN orders o ON pp.point_id = o.pickup_point_id AND o.order_status = 'Arrived_At_Point'
            GROUP BY pp.point_id, pp.capacity
        """)
        stats = cursor.fetchall()
        for row in stats:
            pid = row["point_id"]
            cap = row["capacity"]
            cnt = min(row["cnt"], cap)  # 不能超过容量（防 check constraint 冲突）
            cursor.execute(
                "UPDATE pickup_points SET current_packages = %s WHERE point_id = %s",
                (cnt, pid)
            )
        conn.commit()
        print(f"   已更新 {len(stats)} 个寄存点的包裹计数！")
        # 打印爆仓点的最终饱和度
        for row in stats:
            if row["point_id"] == overload_point_id:
                real_cnt = min(row["cnt"], row["capacity"])
                pct = real_cnt / row["capacity"] * 100
                print(f"   [爆仓] 3期智能寄存柜: {real_cnt}/{row['capacity']} = {pct:.1f}% ")
                if pct > 80:
                    print(f"   [成功] 饱和度超过80%! 大屏将显示红色爆仓警告!")
                break


# ------------------------------------------------------------------
# 主函数
# ------------------------------------------------------------------
def main():
    start_time = time.time()
    print("\n" + "★" * 30)
    print("   🚀 校园外卖模拟数据生成器启动！")
    print("★" * 30)

    conn = get_connection()
    try:
        # 步骤 0：清理旧数据（修复乱码脏数据）
        clean_old_data(conn)

        # 步骤 1：50个学生
        generate_users(conn, 50)

        # 步骤 2：15个商家
        generate_merchants(conn, 15)

        # 步骤 3：每个商家5道菜品
        generate_dishes(conn, 5)

        # 步骤 4：1000条订单流水
        overload_point_id = generate_orders(conn, 1000)

        # 步骤 5：同步寄存点包裹计数（确保大屏正确显示饱和度）
        sync_pickup_packages(conn, overload_point_id)

        elapsed = time.time() - start_time
        print("\n" + "=" * 60)
        print(f"🎉 全部数据生成完毕！耗时: {elapsed:.2f} 秒")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
