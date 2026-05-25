# -*- coding: utf-8 -*-
"""
=================================================================
项目名称：校园外卖两段式配送数据库系统 (campus_delivery_db)
文件名称：generate_mock_data.py
功能描述：使用真实中文词库生成海量模拟数据用于答辩大屏展示
          包含 100用户 / 20商家(各8菜品) / 5000历史订单流水
          15名骑手 / 12个寄存点
适用环境：Python 3.8+ / pymysql / faker
=================================================================
"""

import sys
import io

# ---- 解决 Windows 终端中文乱码 ----
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

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

fake = Faker("zh_CN")

# ==================================================================
# 真实中文姓名库（60个真实校园风姓名）
# ==================================================================
CAMPUS_NAMES = [
    "张伟", "王芳", "李娜", "刘洋", "陈静", "杨磊", "赵敏", "黄磊",
    "周杰", "吴昊", "徐明", "孙丽", "马超", "朱婷", "胡涛", "郭晶",
    "林峰", "何雪", "高峰", "罗强", "梁敏", "宋阳", "唐燕", "韩冰",
    "曹鑫", "邓丽", "许杰", "彭娟", "苏畅", "潘浩", "田甜", "董亮",
    "范琪", "蔡健", "袁媛", "夏雨", "方静", "石磊", "谭飞", "汪洁",
    "余波", "廖辉", "邹霞", "陆勇", "孔慧", "白梅", "邱毅", "龚倩",
    "岳鹏", "顾雪", "段鑫", "雷杰", "侯涛", "龙敏", "向晨", "文静",
    "姜涛", "乔羽", "安琪", "司马悦",
]
DORM_ZONES = ["1期","2期","3期","4期","5期","6期","7期","8期","A区","B区","C区","D区"]

# ==================================================================
# 工具函数：连接数据库
# ==================================================================
def get_connection():
    return pymysql.connect(**DB_CONFIG)


# ------------------------------------------------------------------
# 步骤 0：清理旧数据
# ------------------------------------------------------------------
def clean_old_data(conn):
    """清空所有涉及的表，避免外键冲突"""
    print("=" * 60)
    print("[步骤 0] 正在清理旧数据……")
    with conn.cursor() as cursor:
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        cursor.execute("TRUNCATE TABLE order_items")
        cursor.execute("TRUNCATE TABLE orders")
        cursor.execute("TRUNCATE TABLE dishes")
        cursor.execute("TRUNCATE TABLE merchants")
        cursor.execute("TRUNCATE TABLE users")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    conn.commit()
    print("[完成] 旧数据已全部清空！")
    print("=" * 60)


# ------------------------------------------------------------------
# 步骤 1：生成学生数据 (100条)
# ------------------------------------------------------------------
def generate_users(conn, num=100):
    print(f"\n[步骤 1] 正在生成 {num} 个学生用户……")
    sql = """INSERT INTO users (username, phone, dorm_building, room_number, balance)
             VALUES (%s, %s, %s, %s, %s)"""
    data = []
    used_phones = set()
    for i in range(num):
        username = CAMPUS_NAMES[i % len(CAMPUS_NAMES)]
        while True:
            phone = f"1{random.choice(['38','39','55','77','88','35','36','50','51','52'])}{random.randint(10000000,99999999):08d}"[:11]
            if phone not in used_phones:
                used_phones.add(phone)
                break
        building = f"{random.choice(DORM_ZONES)}{random.randint(1,18)}栋"
        room = f"{random.randint(1,7)}{random.choice(['A','B','C','D'])}{random.randint(1,35):02d}"
        balance = round(random.uniform(30, 800), 2)
        data.append((username, phone, building, room, balance))

    with conn.cursor() as cursor:
        cursor.executemany(sql, data)
    conn.commit()
    print(f"[完成] 成功插入 {num} 个学生用户！")


# ------------------------------------------------------------------
# 步骤 2：生成商家数据 (20条)
# ------------------------------------------------------------------
def generate_merchants(conn, num=20):
    print(f"\n[步骤 2] 正在生成 {num} 个商家……")
    prefix_list = ["好再来", "天天", "一品", "香满园", "味美滋",
                   "食尚", "舌尖", "小当家", "阿妈", "旺角",
                   "老街", "校园", "学子", "翰林", "状元",
                   "川湘", "粤港", "东北", "西北", "江南"]
    suffix_list = ["麻辣烫", "黄焖鸡", "奶茶店", "饺子馆", "盖浇饭",
                   "米线店", "炸鸡店", "烘焙坊", "水果捞", "面馆",
                   "煲仔饭", "寿司店", "麻辣香锅", "烤鱼店", "煎饼果子",
                   "冒菜馆", "螺蛳粉", "炒饭店", "瓦罐汤", "烤串店"]
    sql = """INSERT INTO merchants (merchant_name, phone, address, rating)
             VALUES (%s, %s, %s, %s)"""
    data = []
    used_names = set()
    used_phones = set()
    for _ in range(num):
        while True:
            name = f"{random.choice(prefix_list)}{random.choice(suffix_list)}"
            if name not in used_names:
                used_names.add(name)
                break
        while True:
            phone = f"1{random.choice(['38','39','55','77','88'])}{random.randint(10000000,99999999):08d}"[:11]
            if phone not in used_phones:
                used_phones.add(phone)
                break
        addr = f"{random.choice(['丁香餐厅','玫瑰餐厅','紫荆餐厅','下沉广场','综合楼','学子餐厅'])}{random.choice(['一楼','二楼','三楼','负一楼','负二楼'])}{random.choice(['核心区','侧廊','尽头','入口处','天桥旁'])}"
        rating = round(random.uniform(3.5, 5.0), 1)
        data.append((name, phone, addr, rating))

    with conn.cursor() as cursor:
        cursor.executemany(sql, data)
    conn.commit()
    print(f"[完成] 成功插入 {num} 个商家！")


# ------------------------------------------------------------------
# 步骤 3：生成菜品数据 (每个商家8道菜，共160道)
# ------------------------------------------------------------------
def generate_dishes(conn, dishes_per_merchant=8):
    print(f"\n[步骤 3] 正在为每个商家生成 {dishes_per_merchant} 道菜品……")
    dish_names = [
        "经典麻辣烫", "番茄牛腩面", "宫保鸡丁饭", "鱼香肉丝饭", "糖醋里脊饭",
        "酸菜鱼米线", "香辣鸡腿堡", "珍珠奶茶", "芒果冰沙", "鸡蛋灌饼",
        "牛肉拉面", "蛋炒饭(加蛋)", "葱油拌面", "小笼包(8只)", "煎饺(12只)",
        "烤冷面(加肠)", "手抓饼(加蛋)", "皮蛋瘦肉粥", "豆浆油条套餐", "卤肉饭",
        "咖喱鸡肉饭", "黑椒牛柳意面", "芝士焗饭", "日式拉面", "韩式拌饭",
        "铁板牛肉饭", "红烧排骨饭", "酸辣土豆丝", "干锅手撕包菜", "麻婆豆腐饭",
        "水煮鱼片", "蒜蓉生蚝(6个)", "烤茄子", "羊肉串(10串)", "章鱼小丸子",
        "双皮奶", "杨枝甘露", "烧仙草", "芋圆奶茶", "抹茶拿铁",
        "奥尔良烤鸡腿", "盐酥鸡", "甘梅地瓜条", "花甲粉丝", "锡纸金针菇",
        "螺蛳粉(经典)", "炸酱面", "热干面", "担担面", "油泼面",
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
            price = round(random.uniform(8, 35), 2)
            stock = random.choice([100, 150, 200, 300, 500, 800, 1000])
            status = 1
            data.append((mid, name, price, stock, status))

    with conn.cursor() as cursor:
        cursor.executemany(sql, data)
    conn.commit()
    total = len(data)
    print(f"[完成] 成功插入 {total} 道菜品！")


# ------------------------------------------------------------------
# 步骤 4：生成订单流水 (5000条) + 明细
# ------------------------------------------------------------------
def generate_orders(conn, num_orders=5000):
    print(f"\n[步骤 4] 正在生成 {num_orders} 条历史订单流水（含明细）……")

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

    # 找出"3期智能寄存柜"的 ID（用来制造爆仓危机）容量=80
    overload_point_id = None
    for p in points_data:
        if "3期" in p["point_name"]:
            overload_point_id = p["point_id"]
            break
    if overload_point_id is None:
        overload_point_id = point_ids[0]

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
        ("Paid", 3),
        ("Stage1_Assigned", 5),
        ("Arrived_At_Point", 12),
        ("Stage2_Assigned", 15),
        ("Completed", 65),  # 大半已完成，让数据好看
    ]
    status_list = [s for s, w in status_weights for _ in range(w)]

    OVERLOAD_COUNT = 72  # 3期容量80，塞72个到寄存点 = 90%
    print(f"\n   [爆仓] 正在向 '3期智能寄存柜' 注入 {OVERLOAD_COUNT} 个滞留包裹……")

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

            # ---- 构造时间线：跨越 120 天（约一个学期），按真实分布加权 ----
            # 越近的订单越多（模拟业务增长趋势），使用指数分布让数据更真实
            # 0-30天: 40%, 30-60天: 30%, 60-90天: 20%, 90-120天: 10%
            rand_val = random.random()
            if rand_val < 0.40:
                days_ago = random.randint(0, 30)
            elif rand_val < 0.70:
                days_ago = random.randint(31, 60)
            elif rand_val < 0.90:
                days_ago = random.randint(61, 90)
            else:
                days_ago = random.randint(91, 120)

            created_at = now - timedelta(
                days=days_ago,
                hours=random.randint(8, 22),   # 营业时间 8:00-22:00
                minutes=random.randint(0, 59),
                seconds=random.randint(0, 59),
            )

            stage1_completed_at = None
            stage2_completed_at = None

            # ---- 根据订单状态设置时间戳 ----
            # Stage1_Assigned: 干线还在配送中，stage1_completed_at 应为 NULL
            # Arrived_At_Point: 干线已完成，stage1_completed_at 应设置
            # Stage2_Assigned: 干线已完成，stage1_completed_at 应设置
            # Completed: 两段都已完成
            if order_status in ("Arrived_At_Point", "Stage2_Assigned", "Completed"):
                stage1_completed_at = created_at + timedelta(minutes=random.randint(10, 40))

            if order_status == "Completed":
                stage2_completed_at = stage1_completed_at + timedelta(minutes=random.randint(5, 25))

            # ---- 拼装菜品明细 ----
            available_dishes = dishes_by_merchant.get(merchant_id, [])
            if not available_dishes:
                continue

            selected_dish = random.choice(available_dishes)
            quantity = random.randint(1, 3)
            price_at_order = float(selected_dish["price"])
            total_amount = round(price_at_order * quantity, 2)

            # ---- 根据订单状态骑手指派 ----
            # Paid: 刚支付，尚未分配任何骑手
            # Stage1_Assigned: 仅分配干线骑手（stage1），楼栋骑手（stage2）为 NULL
            # Arrived_At_Point: 干线已完成，干线骑手已释放，等待楼栋骑手
            # Stage2_Assigned: 已分配楼栋骑手（stage2），干线骑手已释放
            # Completed: 两段都已完成，骑手均已释放
            stage1_rider = None
            stage2_rider = None
            if order_status == "Stage1_Assigned":
                stage1_rider = random.choice(trunk_riders) if trunk_riders else None
            elif order_status == "Stage2_Assigned":
                stage2_rider = random.choice(floor_riders) if floor_riders else None
            elif order_status == "Arrived_At_Point":
                # 爆仓订单：干线已完成但滞留寄存点，无骑手占用
                pass
            elif order_status == "Completed":
                # 已完成订单：骑手均已释放
                pass
            # Paid 状态：两个骑手均为 NULL


            cursor.execute(order_insert_sql, (
                user_id, merchant_id, point_id, total_amount, order_status,
                stage1_rider, stage2_rider,
                created_at, stage1_completed_at, stage2_completed_at,
            ))
            order_id = cursor.lastrowid

            cursor.execute(item_insert_sql, (order_id, selected_dish["dish_id"], quantity, price_at_order))

            if (order_index + 1) % 200 == 0 or order_index == num_orders - 1:
                conn.commit()
                progress = order_index + 1
                print(f"   [进度] {progress}/{num_orders} 条订单已生成 ({progress*100/num_orders:.0f}%)")

    # ---- 更新骑手状态 ----
    print(f"\n   [骑手] 正在更新骑手配送状态……")
    with conn.cursor() as cursor:
        cursor.execute("""
            UPDATE riders r
            SET r.status = 'Delivering'
            WHERE r.rider_id IN (
                SELECT rider_id FROM (
                    SELECT o.stage1_rider_id AS rider_id
                    FROM orders o
                    WHERE o.order_status NOT IN ('Completed', 'Cancelled') AND o.stage1_rider_id IS NOT NULL
                    UNION
                    SELECT o.stage2_rider_id AS rider_id
                    FROM orders o
                    WHERE o.order_status NOT IN ('Completed', 'Cancelled') AND o.stage2_rider_id IS NOT NULL
                ) AS active
            )
        """)
        affected = cursor.rowcount
        conn.commit()
    print(f"   [骑手] {affected} 名骑手状态已设为配送中")

    print(f"[完成] 成功插入 {num_orders} 条订单及对应明细！")
    return overload_point_id


# ------------------------------------------------------------------
# 步骤 5：同步寄存点包裹计数
# ------------------------------------------------------------------
def sync_pickup_packages(conn, overload_point_id):
    print(f"\n[步骤 5] 正在同步寄存点包裹计数……")
    with conn.cursor() as cursor:
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
            cnt = min(row["cnt"], cap)
            cursor.execute(
                "UPDATE pickup_points SET current_packages = %s WHERE point_id = %s",
                (cnt, pid)
            )
        conn.commit()
        print(f"   已更新 {len(stats)} 个寄存点的包裹计数！")
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
    print("\n" + "=" * 30)
    print("   校园外卖模拟数据生成器启动！")
    print("=" * 30)

    conn = get_connection()
    try:
        clean_old_data(conn)

        generate_users(conn, 100)
        generate_merchants(conn, 20)
        generate_dishes(conn, 8)
        overload_point_id = generate_orders(conn, 5000)
        sync_pickup_packages(conn, overload_point_id)

        elapsed = time.time() - start_time
        print("\n" + "=" * 60)
        print(f"全部数据生成完毕！耗时: {elapsed:.2f} 秒")
        print("=" * 60)

    except Exception as e:
        print(f"\n[错误] 发生错误: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
