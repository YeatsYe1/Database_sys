# -*- coding: utf-8 -*-
"""数据检查脚本：快速验证各表数据量 + 寄存点饱和度"""

import sys
import io

# ---- 解决 Windows 终端中文乱码 ----
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

import pymysql
import os
from dotenv import load_dotenv

# 使用绝对路径加载 .env 文件
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

def main():
    conn = None
    try:
        conn = pymysql.connect(
            host=os.getenv('MYSQL_HOST', 'localhost'),
            user=os.getenv('MYSQL_USER', 'root'),
            password=os.getenv('MYSQL_PASSWORD'),
            database=os.getenv('MYSQL_DATABASE', 'campus_delivery_db'),
            charset=os.getenv('MYSQL_CHARSET', 'utf8mb4'),
        )
        with conn.cursor() as cur:
            cur.execute('SELECT COUNT(*) FROM users'); u = cur.fetchone()[0]
            cur.execute('SELECT COUNT(*) FROM merchants'); m = cur.fetchone()[0]
            cur.execute('SELECT COUNT(*) FROM orders'); o = cur.fetchone()[0]
            cur.execute('SELECT COUNT(*) FROM dishes'); d = cur.fetchone()[0]
            cur.execute('SELECT COUNT(*) FROM riders'); r = cur.fetchone()[0]
            cur.execute('SELECT COUNT(*) FROM pickup_points'); p = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM riders WHERE status='Delivering'"); rd = cur.fetchone()[0]
            cur.execute('SELECT point_name, current_packages, capacity FROM pickup_points')
            points = cur.fetchall()

        print(f'学生: {u} 人')
        print(f'商家: {m} 家')
        print(f'菜品: {d} 道')
        print(f'订单: {o} 单')
        print(f'寄存点: {p} 个')
        print(f'骑手: {r} 人, 配送中: {rd} 人')
        print('寄存点饱和度:')
        for pt in points:
            print(f'  {pt[0]}: {pt[1]}/{pt[2]} ({pt[1]/pt[2]*100:.1f}%)')
    except Exception as e:
        print(f"[错误] 数据库检查失败: {e}")
        raise
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
