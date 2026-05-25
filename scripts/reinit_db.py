"""用 Python 重建完整数据库（兼容 pymysql，跳过 DELIMITER 语法）"""
import sys
import io

# ---- 解决 Windows 终端中文乱码 ----
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

import pymysql, os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

PASSWORD = os.getenv("MYSQL_PASSWORD")
HOST = os.getenv("MYSQL_HOST", "localhost")
USER = os.getenv("MYSQL_USER", "root")

conn = pymysql.connect(host=HOST, user=USER, password=PASSWORD, charset="utf8mb4")
cur = conn.cursor()
cur.execute("DROP DATABASE IF EXISTS campus_delivery_db")
cur.execute("CREATE DATABASE campus_delivery_db DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci")
cur.execute("USE campus_delivery_db")

# ==================== 创建所有表 ====================
tables = [

    # users
    """CREATE TABLE users (
        user_id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(50) NOT NULL,
        phone VARCHAR(20) NOT NULL UNIQUE,
        dorm_building VARCHAR(20) NOT NULL,
        room_number VARCHAR(10) NOT NULL,
        balance DECIMAL(10,2) DEFAULT 100.00 CHECK (balance >= 0),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
    # merchants
    """CREATE TABLE merchants (
        merchant_id INT AUTO_INCREMENT PRIMARY KEY,
        merchant_name VARCHAR(100) NOT NULL,
        phone VARCHAR(20) NOT NULL,
        address VARCHAR(200) NOT NULL,
        rating DECIMAL(2,1) DEFAULT 5.0 CHECK (rating >= 1.0 AND rating <= 5.0),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
    # dishes
    """CREATE TABLE dishes (
        dish_id INT AUTO_INCREMENT PRIMARY KEY,
        merchant_id INT NOT NULL,
        dish_name VARCHAR(100) NOT NULL,
        price DECIMAL(8,2) NOT NULL CHECK (price > 0),
        stock INT NOT NULL DEFAULT 0 CHECK (stock >= 0),
        status TINYINT DEFAULT 1 CHECK (status IN (0, 1)),
        CONSTRAINT fk_dish_merchant FOREIGN KEY (merchant_id) REFERENCES merchants(merchant_id) ON DELETE RESTRICT ON UPDATE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
    # pickup_points
    """CREATE TABLE pickup_points (
        point_id INT AUTO_INCREMENT PRIMARY KEY,
        point_name VARCHAR(50) NOT NULL,
        location VARCHAR(200) NOT NULL,
        capacity INT NOT NULL,
        current_packages INT DEFAULT 0 CHECK (current_packages >= 0),
        CONSTRAINT chk_capacity CHECK (current_packages <= capacity)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
    # riders
    """CREATE TABLE riders (
        rider_id INT AUTO_INCREMENT PRIMARY KEY,
        rider_name VARCHAR(50) NOT NULL,
        phone VARCHAR(20) NOT NULL UNIQUE,
        rider_type ENUM('Stage1_Trunk', 'Stage2_Floor') NOT NULL,
        status ENUM('Idle', 'Delivering', 'Offline') DEFAULT 'Idle'
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
    # orders
    """CREATE TABLE orders (
        order_id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        merchant_id INT NOT NULL,
        pickup_point_id INT NOT NULL,
        total_amount DECIMAL(10,2) NOT NULL DEFAULT 0.00,
        order_status ENUM('Paid','Stage1_Assigned','Arrived_At_Point','Stage2_Assigned','Completed','Cancelled') DEFAULT 'Paid',
        stage1_rider_id INT DEFAULT NULL,
        stage2_rider_id INT DEFAULT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        stage1_completed_at TIMESTAMP NULL DEFAULT NULL,
        stage2_completed_at TIMESTAMP NULL DEFAULT NULL,
        CONSTRAINT fk_order_user FOREIGN KEY (user_id) REFERENCES users(user_id),
        CONSTRAINT fk_order_merchant FOREIGN KEY (merchant_id) REFERENCES merchants(merchant_id),
        CONSTRAINT fk_order_point FOREIGN KEY (pickup_point_id) REFERENCES pickup_points(point_id),
        CONSTRAINT fk_order_rider1 FOREIGN KEY (stage1_rider_id) REFERENCES riders(rider_id),
        CONSTRAINT fk_order_rider2 FOREIGN KEY (stage2_rider_id) REFERENCES riders(rider_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
    # order_items
    """CREATE TABLE order_items (
        item_id INT AUTO_INCREMENT PRIMARY KEY,
        order_id INT NOT NULL,
        dish_id INT NOT NULL,
        quantity INT NOT NULL CHECK (quantity > 0),
        price_at_order DECIMAL(8,2) NOT NULL,
        CONSTRAINT fk_item_order FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
        CONSTRAINT fk_item_dish FOREIGN KEY (dish_id) REFERENCES dishes(dish_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
]

for t in tables:
    cur.execute(t)

# 建索引
cur.execute("CREATE INDEX idx_orders_status ON orders(order_status)")
cur.execute("CREATE INDEX idx_orders_created ON orders(created_at)")
cur.execute("CREATE INDEX idx_dishes_merchant ON dishes(merchant_id, status)")

# ==================== 创建防超卖触发器（核心亮点） ====================
# 触发器 1：插入订单明细前检查库存和下架状态
cur.execute("""
CREATE TRIGGER trg_check_dish_stock_before_order
BEFORE INSERT ON order_items
FOR EACH ROW
BEGIN
    DECLARE v_stock INT;
    DECLARE v_status TINYINT;
    SELECT stock, status INTO v_stock, v_status
    FROM dishes WHERE dish_id = NEW.dish_id FOR UPDATE;
    IF v_status = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '下单失败：您选购的商品已下架！';
    END IF;
    IF v_stock < NEW.quantity THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '下单失败：手慢了！部分商品库存不足！';
    END IF;
END
""")

# 触发器 2：下单成功后自动扣减库存
cur.execute("""
CREATE TRIGGER trg_reduce_dish_stock_after_order
AFTER INSERT ON order_items
FOR EACH ROW
BEGIN
    UPDATE dishes SET stock = stock - NEW.quantity WHERE dish_id = NEW.dish_id;
END
""")

# ==================== 创建存储过程（业务流引擎） ====================

# 存储过程 1：高并发原子性下单（含完整事务回滚）
cur.execute("""
CREATE PROCEDURE sp_create_order(
    IN p_user_id INT,
    IN p_merchant_id INT,
    IN p_point_id INT,
    IN p_dish_id INT,
    IN p_quantity INT,
    OUT o_order_id INT
)
BEGIN
    DECLARE v_dish_price DECIMAL(8,2);
    DECLARE v_total_amount DECIMAL(10,2);
    DECLARE v_user_balance DECIMAL(10,2);
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    START TRANSACTION;
    SELECT price INTO v_dish_price FROM dishes WHERE dish_id = p_dish_id;
    SET v_total_amount = v_dish_price * p_quantity;
    SELECT balance INTO v_user_balance FROM users WHERE user_id = p_user_id;
    IF v_user_balance < v_total_amount THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '校园卡余额不足，扣款失败！';
    END IF;
    UPDATE users SET balance = balance - v_total_amount WHERE user_id = p_user_id;
    INSERT INTO orders (user_id, merchant_id, pickup_point_id, total_amount, order_status)
    VALUES (p_user_id, p_merchant_id, p_point_id, v_total_amount, 'Paid');
    SET o_order_id = LAST_INSERT_ID();
    INSERT INTO order_items (order_id, dish_id, quantity, price_at_order)
    VALUES (o_order_id, p_dish_id, p_quantity, v_dish_price);
    COMMIT;
END
""")

# 存储过程 2：第一段配送完成 → 到达寄存点
cur.execute("""
CREATE PROCEDURE sp_arrive_at_pickup_point(IN p_order_id INT)
BEGIN
    DECLARE v_point_id INT;
    DECLARE v_rider_id INT;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    START TRANSACTION;
    SELECT pickup_point_id, stage1_rider_id INTO v_point_id, v_rider_id 
    FROM orders WHERE order_id = p_order_id;
    UPDATE orders SET order_status = 'Arrived_At_Point', stage1_completed_at = CURRENT_TIMESTAMP
    WHERE order_id = p_order_id;
    IF v_rider_id IS NOT NULL THEN
        UPDATE riders SET status = 'Idle' WHERE rider_id = v_rider_id;
    END IF;
    UPDATE pickup_points SET current_packages = current_packages + 1 WHERE point_id = v_point_id;
    COMMIT;
END
""")

# 存储过程 3：第二段配送完成 → 送达学生
cur.execute("""
CREATE PROCEDURE sp_stage2_deliver(IN p_order_id INT)
BEGIN
    DECLARE v_point_id INT;
    DECLARE v_rider_id INT;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    START TRANSACTION;
    SELECT pickup_point_id, stage2_rider_id INTO v_point_id, v_rider_id 
    FROM orders WHERE order_id = p_order_id;
    UPDATE orders SET order_status = 'Completed', stage2_completed_at = CURRENT_TIMESTAMP
    WHERE order_id = p_order_id;
    IF v_rider_id IS NOT NULL THEN
        UPDATE riders SET status = 'Idle' WHERE rider_id = v_rider_id;
    END IF;
    UPDATE pickup_points SET current_packages = current_packages - 1 
    WHERE point_id = v_point_id AND current_packages > 0;
    COMMIT;
END
""")

# 存储过程 4：取消订单（退款+恢复库存+释放骑手）
cur.execute("""
CREATE PROCEDURE sp_cancel_order(IN p_order_id INT)
BEGIN
    DECLARE v_user_id INT;
    DECLARE v_total DECIMAL(10,2);
    DECLARE v_status VARCHAR(20);
    DECLARE v_rider1 INT;
    DECLARE v_rider2 INT;
    DECLARE v_point_id INT;
    DECLARE done INT DEFAULT 0;
    DECLARE v_dish_id INT;
    DECLARE v_qty INT;
    DECLARE cur CURSOR FOR 
        SELECT dish_id, quantity FROM order_items WHERE order_id = p_order_id;
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = 1;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    START TRANSACTION;
    SELECT user_id, total_amount, order_status, stage1_rider_id, stage2_rider_id, pickup_point_id
    INTO v_user_id, v_total, v_status, v_rider1, v_rider2, v_point_id
    FROM orders WHERE order_id = p_order_id;
    IF v_status IN ('Completed', 'Cancelled') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '该订单无法取消';
    END IF;
    UPDATE users SET balance = balance + v_total WHERE user_id = v_user_id;
    OPEN cur;
    read_loop: LOOP
        FETCH cur INTO v_dish_id, v_qty;
        IF done THEN LEAVE read_loop; END IF;
        UPDATE dishes SET stock = stock + v_qty WHERE dish_id = v_dish_id;
    END LOOP;
    CLOSE cur;
    IF v_status = 'Arrived_At_Point' OR v_status = 'Stage2_Assigned' THEN
        UPDATE pickup_points SET current_packages = current_packages - 1 
        WHERE point_id = v_point_id AND current_packages > 0;
    END IF;
    IF v_rider1 IS NOT NULL THEN
        UPDATE riders SET status = 'Idle' WHERE rider_id = v_rider1;
    END IF;
    IF v_rider2 IS NOT NULL THEN
        UPDATE riders SET status = 'Idle' WHERE rider_id = v_rider2;
    END IF;
    UPDATE orders SET order_status = 'Cancelled' WHERE order_id = p_order_id;
    COMMIT;
END
""")

# ==================== 创建大屏视图 ====================

# 视图 1：寄存点饱和度分析
cur.execute("""
CREATE VIEW vw_pickup_point_analytics AS
SELECT 
    p.point_id,
    p.point_name,
    p.capacity AS max_capacity,
    p.current_packages,
    ROUND((p.current_packages / p.capacity) * 100, 2) AS saturation_pct,
    COALESCE(sub.backlog_count, 0) AS backlog_count
FROM pickup_points p
LEFT JOIN (
    SELECT pickup_point_id, COUNT(*) AS backlog_count
    FROM orders
    WHERE order_status = 'Arrived_At_Point'
    GROUP BY pickup_point_id
) sub ON p.point_id = sub.pickup_point_id
""")

# 视图 2：商户销售排行
cur.execute("""
CREATE VIEW vw_merchant_sales_rank AS
SELECT 
    m.merchant_id,
    m.merchant_name,
    COUNT(DISTINCT o.order_id) AS total_orders,
    IFNULL(SUM(o.total_amount), 0) AS total_sales,
    RANK() OVER (ORDER BY IFNULL(SUM(o.total_amount), 0) DESC) AS sales_rank
FROM merchants m
LEFT JOIN orders o ON m.merchant_id = o.merchant_id AND o.order_status = 'Completed'
GROUP BY m.merchant_id
""")

# 种子数据：3个学生

for u in [('张三','13800138001','1期5栋','A302',250.00),('李四','13800138002','1期5栋','B511',15.00),('王五','13800138003','2期12栋','404',500.00)]:
    cur.execute("INSERT INTO users (username,phone,dorm_building,room_number,balance) VALUES (%s,%s,%s,%s,%s)", u)

# 种子数据：3个商家
for m in [('一号黄焖鸡米饭','17711112222','丁香餐厅一楼3号档口',4.8),('川湘木桶饭','17711113333','玫瑰餐厅二楼核心区',4.6),('蜜雪冰城校园店','17711114444','下沉广场天桥旁',4.9)]:
    cur.execute("INSERT INTO merchants (merchant_name,phone,address,rating) VALUES (%s,%s,%s,%s)", m)

# 种子数据：4个菜品
cur.execute("INSERT INTO dishes (merchant_id,dish_name,price,stock,status) VALUES (1,'经典大份黄焖鸡(配饭)',18.00,50,1)")
cur.execute("INSERT INTO dishes (merchant_id,dish_name,price,stock,status) VALUES (1,'香辣金针菇肥牛饭',22.00,0,1)")
cur.execute("INSERT INTO dishes (merchant_id,dish_name,price,stock,status) VALUES (2,'辣椒炒肉木桶饭',15.00,100,1)")
cur.execute("INSERT INTO dishes (merchant_id,dish_name,price,stock,status) VALUES (3,'冰鲜柠檬水(超大杯)',4.00,200,1)")

# 12个寄存点
points = [
    ('1期智能寄存柜','1期5栋与6栋之间车棚旁',80),
    ('2期智能寄存柜','2期12栋宿管值班室对面',80),
    ('3期智能寄存柜','3期8栋楼下大厅',80),
    ('4期智能寄存柜','4期2栋架空层',80),
    ('5期智能寄存柜','5期生活广场东侧',100),
    ('6期智能寄存柜','6期食堂旁',50),
    ('7期智能寄存柜','7期3栋一楼楼梯间',60),
    ('8期智能寄存柜','8期北门快递站旁',120),
    ('A区智能寄存柜','A区综合服务大厅',100),
    ('B区智能寄存柜','B区图书馆负一层',90),
    ('C区智能寄存柜','C区体育馆入口处',70),
    ('D区智能寄存柜','D区研究生公寓大堂',80),
]
for n,l,c in points:
    cur.execute("INSERT INTO pickup_points (point_name,location,capacity,current_packages) VALUES (%s,%s,%s,0)", (n,l,c))

# 15名骑手
riders = [
    ('赵铁柱','15599991111','Stage1_Trunk'),
    ('王大锤','15599992222','Stage1_Trunk'),
    ('李大力','15599994444','Stage1_Trunk'),
    ('周小飞','15599995555','Stage1_Trunk'),
    ('刘强东','15599996666','Stage1_Trunk'),
    ('吴勇军','15599997777','Stage1_Trunk'),
    ('郑明达','15599998888','Stage1_Trunk'),
    ('黄启航','15599999999','Stage1_Trunk'),
    ('牛干劲','15599993333','Stage2_Floor'),
    ('马小跳','15611111111','Stage2_Floor'),
    ('林志远','15611112222','Stage2_Floor'),
    ('张小凡','15611113333','Stage2_Floor'),
    ('陈奕迅','15611114444','Stage2_Floor'),
    ('李逍遥','15611115555','Stage2_Floor'),
    ('赵灵儿','15611116666','Stage2_Floor'),
]
for n,p,t in riders:
    cur.execute("INSERT INTO riders (rider_name,phone,rider_type,status) VALUES (%s,%s,%s,'Idle')", (n,p,t))

conn.commit()
cur.close()
conn.close()
print("[OK] 数据库重建成功！")
print("  - 7 张核心业务表")
print("  - 12 个寄存点")
print("  - 15 名骑手（8名干线 + 7名楼栋）")
print("  - 2 个防超卖触发器（行级锁安全防护）")
print("  - 4 个存储过程（下单/入库/送达/取消）")
print("  - 2 个大屏视图（饱和度分析 + 商户排行）")
print("  现在请运行: python generate_mock_data.py")


