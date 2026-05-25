# -*- coding: utf-8 -*-
"""数据库连接 + 所有数据查询函数"""

import streamlit as st
import pandas as pd
import pymysql
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD"),
    "database": os.getenv("MYSQL_DATABASE", "campus_delivery_db"),
    "charset": os.getenv("MYSQL_CHARSET", "utf8mb4"),
    "use_unicode": True,
    "init_command": "SET NAMES utf8mb4",
}

def get_connection():
    return pymysql.connect(**DB_CONFIG)


def _get_date_option():
    return st.session_state.get("date_filter_opt", "全部数据")


def _build_date_filter_generic(table_alias="o", date_option=None):
    if date_option is None:
        date_option = _get_date_option()
    col = f"{table_alias}.created_at"
    today_sql = f"DATE({col}) = CURDATE()"
    week_sql = f"{col} >= DATE_SUB(NOW(), INTERVAL 7 DAY)"
    month_sql = f"{col} >= DATE_SUB(NOW(), INTERVAL 30 DAY)"
    month_cal = f"DATE_FORMAT({col}, '%Y-%m') = DATE_FORMAT(NOW(), '%Y-%m')"
    mapping = {
        "今天": " AND " + today_sql,
        "最近 7 天": " AND " + week_sql,
        "最近 30 天": " AND " + month_sql,
        "本月": " AND " + month_cal,
        "全部数据": "",
    }
    return mapping.get(date_option, "")


@st.cache_data(ttl=60)
def load_pickup_analytics():
    conn = get_connection()
    try:
        sql = """SELECT point_name, max_capacity, current_packages,
                        saturation_pct, backlog_count
                 FROM vw_pickup_point_analytics"""
        with conn.cursor() as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(rows, columns=columns)
        if not df.empty and 'point_name' in df.columns:
            df['point_name'] = df['point_name'].astype(str)
        return df
    finally:
        conn.close()


@st.cache_data(ttl=60)
def load_merchant_sales_rank():
    conn = get_connection()
    try:
        sql = """SELECT merchant_name, total_orders, total_sales, sales_rank
                 FROM vw_merchant_sales_rank ORDER BY sales_rank"""
        with conn.cursor() as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
        return pd.DataFrame(rows, columns=columns)
    finally:
        conn.close()


@st.cache_data(ttl=60)
def load_order_status_distribution(date_option="全部数据"):
    conn = get_connection()
    try:
        date_filter = _build_date_filter_generic("o", date_option)
        query = f"""SELECT o.order_status, COUNT(*) AS order_count
                    FROM orders o WHERE 1=1 {date_filter}
                    GROUP BY o.order_status ORDER BY order_count DESC"""
        with conn.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
        return pd.DataFrame(rows, columns=columns)
    finally:
        conn.close()


@st.cache_data(ttl=60)
def load_basic_stats(date_option="全部数据"):
    conn = get_connection()
    try:
        date_filter_orders = _build_date_filter_generic("o", date_option)
        stats = {}
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM users")
            stats["total_users"] = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM merchants")
            stats["total_merchants"] = cursor.fetchone()[0]
            cursor.execute(f"SELECT COUNT(*) FROM orders o WHERE 1=1 {date_filter_orders}")
            stats["total_orders"] = cursor.fetchone()[0]
            cursor.execute(f"""SELECT IFNULL(SUM(o.total_amount), 0)
                FROM orders o WHERE o.order_status = 'Completed' {date_filter_orders}""")
            stats["total_revenue"] = cursor.fetchone()[0]
            cursor.execute("""SELECT COUNT(DISTINCT r.rider_id) FROM riders r
                WHERE r.status = 'Delivering'
                   OR r.rider_id IN (
                       SELECT stage1_rider_id FROM orders
                       WHERE order_status NOT IN ('Completed', 'Cancelled') AND stage1_rider_id IS NOT NULL
                       UNION
                       SELECT stage2_rider_id FROM orders
                       WHERE order_status NOT IN ('Completed', 'Cancelled') AND stage2_rider_id IS NOT NULL)""")
            stats["active_riders"] = cursor.fetchone()[0]
            cursor.execute(f"""SELECT COUNT(*) FROM orders o
                WHERE DATE(o.created_at) = CURDATE() {date_filter_orders}""")
            stats["today_orders"] = cursor.fetchone()[0]
        return stats
    finally:
        conn.close()


@st.cache_data(ttl=60)
def load_recent_orders(limit=10, date_option="全部数据"):
    conn = get_connection()
    try:
        date_filter = _build_date_filter_generic("o", date_option)
        query = f"""SELECT o.order_id AS '订单号', u.username AS '学生',
                    m.merchant_name AS '商家', o.total_amount AS '金额(元)',
                    o.order_status AS '状态', o.created_at AS '下单时间_raw'
             FROM orders o
             JOIN users u ON o.user_id = u.user_id
             JOIN merchants m ON o.merchant_id = m.merchant_id
             WHERE 1=1 {date_filter}
             ORDER BY o.created_at DESC LIMIT {limit}"""
        with conn.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(rows, columns=columns)
        if not df.empty and '下单时间_raw' in df.columns:
            df['下单时间'] = pd.to_datetime(df['下单时间_raw']).dt.strftime('%m-%d %H:%M')
            df = df.drop(columns=['下单时间_raw'])
        return df
    finally:
        conn.close()


@st.cache_data(ttl=60)
def load_time_period_distribution(date_option="全部数据"):
    conn = get_connection()
    try:
        date_filter = _build_date_filter_generic("o", date_option)
        query = f"""SELECT
            CASE
                WHEN HOUR(o.created_at) BETWEEN 6 AND 8 THEN '06-09 早餐'
                WHEN HOUR(o.created_at) BETWEEN 9 AND 10 THEN '09-11 上午'
                WHEN HOUR(o.created_at) BETWEEN 11 AND 13 THEN '11-13 午餐高峰'
                WHEN HOUR(o.created_at) BETWEEN 14 AND 16 THEN '14-17 下午'
                WHEN HOUR(o.created_at) BETWEEN 17 AND 19 THEN '17-19 晚餐高峰'
                WHEN HOUR(o.created_at) BETWEEN 20 AND 22 THEN '20-22 夜宵'
                ELSE '其他时段'
            END AS time_period,
            COUNT(*) AS order_count, ROUND(AVG(o.total_amount), 2) AS avg_amount
            FROM orders o WHERE 1=1 {date_filter}
            GROUP BY time_period ORDER BY MIN(HOUR(o.created_at))"""
        with conn.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
        return pd.DataFrame(rows, columns=columns)
    finally:
        conn.close()


@st.cache_data(ttl=60)
def load_merchant_info():
    conn = get_connection()
    try:
        query = """SELECT merchant_id AS '编号', merchant_name AS '店铺名称',
                    phone AS '联系电话', rating AS '评分', created_at AS '入驻时间_raw'
                   FROM merchants ORDER BY merchant_id"""
        with conn.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(rows, columns=columns)
        if not df.empty and '入驻时间_raw' in df.columns:
            df['入驻时间'] = pd.to_datetime(df['入驻时间_raw']).dt.strftime('%Y-%m-%d')
            df = df.drop(columns=['入驻时间_raw'])
        return df
    finally:
        conn.close()


@st.cache_data(ttl=60)
def load_student_info():
    conn = get_connection()
    try:
        query = """SELECT user_id AS '学号', username AS '姓名', phone AS '手机号',
                    dorm_building AS '宿舍楼栋', balance AS '校园卡余额(元)',
                    created_at AS '注册时间_raw'
                   FROM users ORDER BY user_id"""
        with conn.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(rows, columns=columns)
        if not df.empty and '注册时间_raw' in df.columns:
            df['注册时间'] = pd.to_datetime(df['注册时间_raw']).dt.strftime('%Y-%m-%d')
            df = df.drop(columns=['注册时间_raw'])
        return df
    finally:
        conn.close()


@st.cache_data(ttl=60)
def load_merchant_dishes():
    conn = get_connection()
    try:
        query = """SELECT d.dish_id AS '菜品编号', d.dish_name AS '菜品名称',
                    d.price AS '单价(元)', d.stock AS '库存',
                    m.merchant_name AS '所属商家'
                   FROM dishes d JOIN merchants m ON d.merchant_id = m.merchant_id
                   ORDER BY m.merchant_name, d.dish_id"""
        with conn.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
        return pd.DataFrame(rows, columns=columns)
    finally:
        conn.close()


@st.cache_data(ttl=60)
def load_rider_info():
    conn = get_connection()
    try:
        query = """SELECT rider_id AS '编号', rider_name AS '姓名',
                    phone AS '联系电话', rider_type AS '分工', status AS '状态'
                   FROM riders ORDER BY rider_id"""
        with conn.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(rows, columns=columns)
        if not df.empty:
            type_map = {'Stage1_Trunk': '🚚 干线骑手', 'Stage2_Floor': '🏠 楼栋骑手'}
            status_map = {'Idle': '🟢 空闲', 'Delivering': '🔴 配送中', 'Offline': '⚫ 离线'}
            df['分工'] = df['分工'].map(type_map).fillna(df['分工'])
            df['状态'] = df['状态'].map(status_map).fillna(df['状态'])
        return df
    finally:
        conn.close()


@st.cache_data(ttl=60)
def load_pickup_point_info():
    conn = get_connection()
    try:
        query = """SELECT point_id AS '编号', point_name AS '站点名称',
                    location AS '位置', capacity AS '最大容量',
                    current_packages AS '当前在库'
                   FROM pickup_points ORDER BY point_id"""
        with conn.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(rows, columns=columns)
        if not df.empty:
            df['饱和度'] = (df['当前在库'] / df['最大容量'] * 100).round(1).astype(str) + '%'
        return df
    finally:
        conn.close()
