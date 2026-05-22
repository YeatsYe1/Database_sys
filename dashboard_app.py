# -*- coding: utf-8 -*-
"""
==================================================================
项目名称：校园外卖两段式配送数据库系统 (campus_delivery_db)
文件名称：dashboard_app.py
功能描述：Streamlit 宽屏网格数据大屏（期末答辩展示）
          + AI 智能数据助手（DeepSeek Text-to-SQL）
设计风格：宽屏网格布局 · 卡片化 · 渐变色 · 爆仓预警
适用环境：Python 3.8+ / streamlit / pymysql / pandas / matplotlib / openai
==================================================================
"""

import streamlit as st
import pandas as pd
import pymysql
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
from datetime import datetime, timedelta
import os
import json
import traceback
from dotenv import load_dotenv
from openai import OpenAI

# ================================================================
# 加载 .env 文件中的环境变量（绝不硬编码密码）
# ================================================================
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# ---------------------------------------------------------------
# Matplotlib 中文字体配置
# ---------------------------------------------------------------
plt.rcParams['axes.unicode_minus'] = False

_CHINESE_FONT_PATHS = [
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\msyhbd.ttc",
    r"C:\Windows\Fonts\simhei.ttf",
    r"C:\Windows\Fonts\msyh.ttf",
    r"C:\Windows\Fonts\SIMHEI.TTF",
]

_FONT_PATH = None
for _fp in _CHINESE_FONT_PATHS:
    if os.path.exists(_fp):
        _FONT_PATH = _fp
        break

if _FONT_PATH:
    fm.fontManager.addfont(_FONT_PATH)
    _fp_obj = fm.FontProperties(fname=_FONT_PATH)
    _font_name = _fp_obj.get_name()
    plt.rcParams['font.family'] = 'sans-serif'
    if _font_name not in plt.rcParams['font.sans-serif']:
        plt.rcParams['font.sans-serif'].insert(0, _font_name)
    FONT_PROP = fm.FontProperties(fname=_FONT_PATH)
else:
    _fallback_names = ['Microsoft YaHei', 'SimHei', 'Noto Sans SC', 'Noto Sans CJK SC', 'SimSun']
    FONT_PROP = fm.FontProperties()
    for _name in _fallback_names:
        try:
            _test_fp = fm.FontProperties(family=_name)
            _test_path = fm.findfont(_test_fp)
            if _test_path:
                plt.rcParams['font.sans-serif'].insert(0, _name)
                plt.rcParams['font.family'] = 'sans-serif'
                FONT_PROP = fm.FontProperties(family=_name)
                break
        except Exception:
            continue

# ================================================================
# 数据库连接配置 — 完全从 .env 读取，绝不硬编码
# ================================================================
DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD"),
    "database": os.getenv("MYSQL_DATABASE", "campus_delivery_db"),
    "charset": "utf8mb4",          # 强制锁死 utf8mb4，杜绝中文乱码
    "use_unicode": True,
    "init_command": "SET NAMES utf8mb4",
}

# ================================================================
# DeepSeek AI 配置 — 从 .env 读取
# ================================================================
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

# ---- 页面路径 ----
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ---- 全局配色方案 ----
COLOR_PRIMARY = "#4F46E5"
COLOR_SECONDARY = "#06B6D4"
COLOR_SUCCESS = "#22C55E"
COLOR_WARNING = "#F59E0B"
COLOR_DANGER = "#EF4444"
COLOR_BG = "#F8FAFC"
COLOR_CARD = "#FFFFFF"
COLOR_TEXT = "#1E293B"

# ---- Streamlit 页面配置 ----
st.set_page_config(
    page_title="校园外卖两段式配送 · 实时数据监控大屏",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---- 自定义全局 CSS ----
st.markdown(f"""
<style>
    .stApp {{
        background: {COLOR_BG};
        font-family: "Microsoft YaHei", "SimHei", "Arial Unicode MS", "Noto Sans CJK SC", sans-serif;
    }}
    body, .stApp, .css-1v0mbdj, .css-18ni7ap {{
        font-family: "Microsoft YaHei", "SimHei", "Arial Unicode MS", "Noto Sans CJK SC", sans-serif;
    }}
    .header-container {{
        background: linear-gradient(135deg, #4F46E5 0%, #06B6D4 100%);
        padding: 2rem 2rem 1.5rem;
        border-radius: 0 0 30px 30px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 20px rgba(79,70,229,0.3);
    }}
    .header-title {{
        color: white;
        font-size: 2rem;
        font-weight: 700;
        text-align: center;
        margin: 0;
        letter-spacing: 1px;
    }}
    .header-sub {{
        color: rgba(255,255,255,0.85);
        text-align: center;
        font-size: 0.9rem;
        margin-top: 0.5rem;
    }}
    .kpi-card {{
        background: {COLOR_CARD};
        padding: 1.2rem 1rem;
        border-radius: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        text-align: center;
        border-left: 4px solid {COLOR_PRIMARY};
        transition: transform 0.2s;
    }}
    .kpi-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 16px rgba(0,0,0,0.1);
    }}
    .kpi-value {{
        font-size: 1.8rem;
        font-weight: 700;
        color: {COLOR_PRIMARY};
    }}
    .kpi-label {{
        font-size: 0.85rem;
        color: #64748B;
        margin-top: 0.2rem;
    }}
    .chart-card {{
        background: {COLOR_CARD};
        border-radius: 16px;
        padding: 1.2rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        margin-bottom: 1rem;
    }}
    .chart-title {{
        font-size: 1.1rem;
        font-weight: 600;
        color: {COLOR_TEXT};
        margin-bottom: 0.8rem;
        padding-left: 0.6rem;
        border-left: 4px solid {COLOR_PRIMARY};
    }}
    .ai-chat-container {{
        background: white;
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        margin-bottom: 1rem;
    }}
    .ai-message {{
        padding: 0.8rem 1rem;
        border-radius: 12px;
        margin-bottom: 0.8rem;
        font-size: 0.9rem;
        line-height: 1.5;
    }}
    .ai-message.user {{
        background: #EEF2FF;
        border-left: 4px solid #4F46E5;
        color: #1E293B;
    }}
    .ai-message.assistant {{
        background: #F0FDF4;
        border-left: 4px solid #22C55E;
        color: #1E293B;
    }}
    .ai-message.sql {{
        background: #F8FAFC;
        border-left: 4px solid #F59E0B;
        font-family: 'Consolas', 'Courier New', monospace;
        font-size: 0.8rem;
        color: #1E293B;
        white-space: pre-wrap;
        overflow-x: auto;
    }}
    .ai-message.error {{
        background: #FEF2F2;
        border-left: 4px solid #EF4444;
        color: #991B1B;
    }}
    .footer {{
        text-align: center;
        color: #94A3B8;
        font-size: 0.8rem;
        padding: 2rem 0 1rem;
        border-top: 1px solid #E2E8F0;
        margin-top: 2rem;
    }}
</style>
""", unsafe_allow_html=True)

# ================================================================
# 数据库连接与缓存查询
# ================================================================

def get_connection():
    """获取数据库连接（统一 charset='utf8mb4' 编码锁死）"""
    return pymysql.connect(**DB_CONFIG)


def _build_date_filter():
    """根据 session 中选中的时间范围生成 SQL 条件"""
    option = st.session_state.get("date_filter_opt", "全部数据")
    today_sql = "DATE(o.created_at) = CURDATE()"
    week_sql = "o.created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)"
    month_sql = "o.created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)"
    month_cal = "DATE_FORMAT(o.created_at, '%Y-%m') = DATE_FORMAT(NOW(), '%Y-%m')"
    mapping = {
        "今天": (" AND " + today_sql, " AND " + today_sql),
        "最近 7 天": (" AND " + week_sql, " AND " + week_sql),
        "最近 30 天": (" AND " + month_sql, " AND " + month_sql),
        "本月": (" AND " + month_cal, " AND " + month_cal),
        "全部数据": ("", ""),
    }
    return mapping.get(option, ("", ""))


def _build_date_filter_generic(table_alias="o"):
    """根据 session 中选中的时间范围生成通用 SQL 条件，可指定表别名"""
    option = st.session_state.get("date_filter_opt", "全部数据")
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
    return mapping.get(option, "")


@st.cache_data(ttl=60)
def load_pickup_analytics():
    """读取寄存点饱和度分析"""
    conn = get_connection()
    try:
        sql = """
            SELECT 
                point_name,
                max_capacity,
                current_packages,
                saturation_pct,
                backlog_count
            FROM vw_pickup_point_analytics
        """
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
    """读取商户销售排行"""
    conn = get_connection()
    try:
        sql = """
            SELECT 
                merchant_name,
                total_orders,
                total_sales,
                sales_rank
            FROM vw_merchant_sales_rank
            ORDER BY sales_rank
        """
        with conn.cursor() as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
        return pd.DataFrame(rows, columns=columns)
    finally:
        conn.close()


@st.cache_data(ttl=60)
def load_order_status_distribution():
    """读取订单状态分布"""
    conn = get_connection()
    try:
        date_filter = _build_date_filter_generic("o")
        query = f"""
            SELECT o.order_status, COUNT(*) AS order_count
            FROM orders o
            WHERE 1=1 {date_filter}
            GROUP BY o.order_status
            ORDER BY order_count DESC
        """
        with conn.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
        return pd.DataFrame(rows, columns=columns)
    finally:
        conn.close()


@st.cache_data(ttl=60)
def load_basic_stats():
    """读取基本统计指标"""
    conn = get_connection()
    try:
        date_filter_orders = _build_date_filter_generic("o")
        stats = {}
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM users")
            stats["total_users"] = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM merchants")
            stats["total_merchants"] = cursor.fetchone()[0]
            cursor.execute(f"SELECT COUNT(*) FROM orders o WHERE 1=1 {date_filter_orders}")
            stats["total_orders"] = cursor.fetchone()[0]
            cursor.execute(f"""
                SELECT IFNULL(SUM(o.total_amount), 0) 
                FROM orders o 
                WHERE o.order_status = 'Completed' {date_filter_orders}
            """)
            stats["total_revenue"] = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM riders WHERE status = 'Delivering'")
            stats["active_riders"] = cursor.fetchone()[0]
            cursor.execute("""
                SELECT COUNT(*) FROM orders 
                WHERE DATE(created_at) = CURDATE()
            """)
            stats["today_orders"] = cursor.fetchone()[0]
        return stats
    finally:
        conn.close()


@st.cache_data(ttl=60)
def load_recent_orders(limit=10):
    """读取最近订单"""
    conn = get_connection()
    try:
        date_filter = _build_date_filter_generic("o")
        query = f"""
            SELECT 
                o.order_id AS '订单号',
                u.username AS '学生',
                m.merchant_name AS '商家',
                o.total_amount AS '金额(元)',
                o.order_status AS '状态',
                DATE_FORMAT(o.created_at, '%%m-%%d %%H:%%i') AS '下单时间'
            FROM orders o
            JOIN users u ON o.user_id = u.user_id
            JOIN merchants m ON o.merchant_id = m.merchant_id
            WHERE 1=1 {date_filter}
            ORDER BY o.created_at DESC
            LIMIT {limit}
        """
        with conn.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
        return pd.DataFrame(rows, columns=columns)
    finally:
        conn.close()


@st.cache_data(ttl=60)
def load_time_period_distribution():
    """读取时段订单分布（早餐/午餐高峰/下午/晚餐高峰/夜宵）"""
    conn = get_connection()
    try:
        date_filter = _build_date_filter_generic("o")
        query = f"""
            SELECT
                CASE
                    WHEN HOUR(o.created_at) BETWEEN 6 AND 8 THEN '06-09 早餐'
                    WHEN HOUR(o.created_at) BETWEEN 9 AND 10 THEN '09-11 上午'
                    WHEN HOUR(o.created_at) BETWEEN 11 AND 13 THEN '11-13 午餐高峰'
                    WHEN HOUR(o.created_at) BETWEEN 14 AND 16 THEN '14-17 下午'
                    WHEN HOUR(o.created_at) BETWEEN 17 AND 19 THEN '17-19 晚餐高峰'
                    WHEN HOUR(o.created_at) BETWEEN 20 AND 22 THEN '20-22 夜宵'
                    ELSE '其他时段'
                END AS time_period,
                COUNT(*) AS order_count,
                ROUND(AVG(o.total_amount), 2) AS avg_amount
            FROM orders o
            WHERE 1=1 {date_filter}
            GROUP BY time_period
            ORDER BY MIN(HOUR(o.created_at))
        """
        with conn.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
        return pd.DataFrame(rows, columns=columns)
    finally:
        conn.close()


# ================================================================
# AI 智能数据助手 — DeepSeek Text-to-SQL
# ================================================================

DB_SCHEMA_DESCRIPTION = """
数据库名称：campus_delivery_db（校园外卖两段式配送系统）

表结构说明：

1. users（学生用户表）
   - user_id: 学生唯一ID (INT, PK)
   - username: 姓名 (VARCHAR)
   - phone: 手机号 (VARCHAR)
   - dorm_building: 宿舍楼栋 (VARCHAR, 如: 1期5栋)
   - room_number: 房间号 (VARCHAR)
   - balance: 校园卡钱包余额 (DECIMAL)
   - created_at: 注册时间 (TIMESTAMP)

2. merchants（商家信息表）
   - merchant_id: 商家唯一ID (INT, PK)
   - merchant_name: 店铺名称 (VARCHAR)
   - phone: 联系电话 (VARCHAR)
   - address: 档口地址 (VARCHAR)
   - rating: 商家评分 (DECIMAL, 1.0-5.0)
   - created_at: 入驻时间 (TIMESTAMP)

3. dishes（菜品表）
   - dish_id: 菜品唯一ID (INT, PK)
   - merchant_id: 所属商家ID (INT, FK)
   - dish_name: 菜品名称 (VARCHAR)
   - price: 单价 (DECIMAL)
   - stock: 当前实时库存 (INT)
   - status: 上架状态 (TINYINT, 0下架/1上架)

4. pickup_points（寄存中转点表）
   - point_id: 寄存点唯一ID (INT, PK)
   - point_name: 寄存点名称 (VARCHAR)
   - location: 具体位置 (VARCHAR)
   - capacity: 最大格子容积 (INT)
   - current_packages: 当前在库件数 (INT)

5. riders（两段式骑手表）
   - rider_id: 骑手唯一ID (INT, PK)
   - rider_name: 骑手姓名 (VARCHAR)
   - phone: 联系电话 (VARCHAR)
   - rider_type: 骑手分工 (ENUM: 'Stage1_Trunk'干线/'Stage2_Floor'楼栋)
   - status: 工作状态 (ENUM: 'Idle'空闲/'Delivering'配送中/'Offline'离线)

6. orders（订单主表 - 核心表）
   - order_id: 订单唯一流水号 (INT, PK)
   - user_id: 下单学生ID (INT, FK)
   - merchant_id: 下单商家ID (INT, FK)
   - pickup_point_id: 指派寄存点ID (INT, FK)
   - total_amount: 总金额 (DECIMAL)
   - order_status: 订单状态 (ENUM: 'Paid'/'Stage1_Assigned'/'Arrived_At_Point'/'Stage2_Assigned'/'Completed'/'Cancelled')
   - stage1_rider_id: 干线骑手ID (INT, FK, nullable)
   - stage2_rider_id: 楼栋骑手ID (INT, FK, nullable)
   - created_at: 下单时间 (TIMESTAMP)
   - stage1_completed_at: 干线送达时间 (TIMESTAMP, nullable)
   - stage2_completed_at: 最终送达时间 (TIMESTAMP, nullable)

7. order_items（订单明细表）
   - item_id: 明细项ID (INT, PK)
   - order_id: 关联订单ID (INT, FK)
   - dish_id: 关联菜品ID (INT, FK)
   - quantity: 购买数量 (INT)
   - price_at_order: 购买时单价快照 (DECIMAL)

重要视图：
- vw_pickup_point_analytics: 寄存点饱和度分析
- vw_merchant_sales_rank: 商户销售排行

注意事项：
- 查询时请使用中文别名
- 金额单位是元（人民币）
- 只允许执行 SELECT 查询，禁止修改数据
"""


def init_deepseek_client():
    """初始化 DeepSeek 客户端"""
    if not DEEPSEEK_API_KEY:
        return None
    return OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url=DEEPSEEK_BASE_URL,
    )


def ai_text_to_sql(user_question: str) -> dict:
    """
    将用户的中文自然语言问题转换为 SQL 并执行
    返回: {"success": bool, "sql": str, "result": list[dict], "error": str}
    """
    client = init_deepseek_client()
    if not client:
        return {
            "success": False,
            "sql": "",
            "result": [],
            "error": "DeepSeek API Key 未配置！请在 .env 文件中设置 DEEPSEEK_API_KEY"
        }

    system_prompt = f"""你是一个专业的 Text-to-SQL 助手。你的任务是将用户的中文问题转换为 MySQL SQL 查询语句。

数据库 Schema：
{DB_SCHEMA_DESCRIPTION}

要求：
1. 只生成 SELECT 查询语句，绝不生成 INSERT/UPDATE/DELETE/DROP/ALTER 等修改语句
2. 给字段起中文别名（使用 AS）
3. 如果问题涉及金额统计，注意只统计 order_status='Completed' 的已完成订单
4. 如果问题不明确，选择最合理的解释
5. 只返回 SQL 语句本身，不要加任何解释或 markdown 标记
6. SQL 语句要兼容 MySQL 8.0 语法"""

    try:
        response = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_question}
            ],
            temperature=0.1,
            max_tokens=1000,
        )
        sql = response.choices[0].message.content.strip()
        sql = sql.replace("```sql", "").replace("```", "").strip()

        if not sql.upper().strip().startswith("SELECT"):
            return {
                "success": False,
                "sql": sql,
                "result": [],
                "error": "AI 生成的不是查询语句，已拦截执行"
            }

        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
            df = pd.DataFrame(rows, columns=columns)
            result = df.to_dict(orient="records")
            return {
                "success": True,
                "sql": sql,
                "result": result,
                "columns": columns,
                "row_count": len(result),
                "error": ""
            }
        except Exception as e:
            return {
                "success": False,
                "sql": sql,
                "result": [],
                "error": f"SQL 执行错误：{str(e)}"
            }
        finally:
            conn.close()

    except Exception as e:
        return {
            "success": False,
            "sql": "",
            "result": [],
            "error": f"AI 调用失败：{str(e)}"
        }


# ================================================================
# 图表美化工具函数
# ================================================================

def style_axis(ax):
    """统一坐标轴美化"""
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#E2E8F0')
    ax.spines['bottom'].set_color('#E2E8F0')
    ax.tick_params(colors='#64748B', labelsize=10)


def render_kpi_row(stats):
    """渲染顶部 KPI 指标行"""
    kpi_items = [
        ("总订单量", f"{int(stats['total_orders'])} 单", COLOR_PRIMARY),
        ("活跃商家", f"{int(stats['total_merchants'])} 家", COLOR_SECONDARY),
        ("在途骑手", f"{int(stats['active_riders'])} 人", COLOR_WARNING),
        ("总营业额", f"\u00a5{float(stats['total_revenue']):,.2f}", COLOR_SUCCESS),
    ]
    cols = st.columns(4)
    for col, (label, value, color) in zip(cols, kpi_items):
        with col:
            st.markdown(f"""
            <div class="kpi-card" style="border-left-color: {color};">
                <div class="kpi-value" style="color: {color};">{value}</div>
                <div class="kpi-label">{label}</div>
            </div>
            """, unsafe_allow_html=True)


def render_pickup_saturation_chart(df_points):
    """渲染寄存点饱和度柱状图 + 爆仓预警"""
    fig, ax = plt.subplots(figsize=(8, 4))
    fig.patch.set_facecolor('none')
    ax.set_facecolor('none')
    names = df_points['point_name'].tolist()
    values = df_points['saturation_pct'].tolist()
    colors_bar = ['#22C55E' if v < 60 else '#F59E0B' if v < 80 else '#EF4444' for v in values]
    bars = ax.bar(names, values, color=colors_bar, width=0.5,
                  edgecolor='white', linewidth=2, zorder=3)
    ax.axhline(y=80, color='#EF4444', linestyle='--', linewidth=1.5,
               alpha=0.7, label='爆仓阈值 80%', zorder=2)
    ax.axhline(y=60, color='#F59E0B', linestyle='--', linewidth=1,
               alpha=0.5, label='预警阈值 60%', zorder=2)
    for bar, v in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
                f'{v:.1f}%', ha='center', va='bottom',
                fontsize=11, fontweight='bold', color='#1E293B',
                fontproperties=FONT_PROP)
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, fontproperties=FONT_PROP)
    ax.set_ylim(0, 105)
    style_axis(ax)
    ax.legend(fontsize=9, loc='upper right', framealpha=0.8, prop=FONT_PROP)
    ax.set_ylabel('饱和度 (%)', fontsize=10, color='#64748B', fontproperties=FONT_PROP)
    st.pyplot(fig, width='stretch')
    plt.close()

    # 爆仓预警：饱和度超过 80% 的寄存点
    overflow_points = df_points[df_points['saturation_pct'] > 80]
    if not overflow_points.empty:
        for _, row in overflow_points.iterrows():
            st.warning(
                f"爆仓预警: {row['point_name']} 饱和度 {row['saturation_pct']:.1f}% "
                f"(已用 {int(row['current_packages'])} / 最大 {int(row['max_capacity'])} 格, "
                f"滞留 {int(row['backlog_count'])} 件)"
            )


def render_merchant_rank_chart(df_merchants):
    """渲染商户销售排行水平柱状图"""
    top10 = df_merchants.head(10).iloc[::-1]
    fig, ax = plt.subplots(figsize=(8, 5))
    fig.patch.set_facecolor('none')
    ax.set_facecolor('none')
    palette = sns.color_palette("viridis", len(top10))[::-1]
    bars = ax.barh(top10['merchant_name'], top10['total_sales'],
                   color=palette, edgecolor='white', linewidth=1.5, height=0.6, zorder=3)
    for bar, (_, row) in zip(bars, top10.iterrows()):
        w = bar.get_width()
        ax.text(w + 10, bar.get_y() + bar.get_height()/2,
                f'\u00a5{w:,.0f}  ({int(row["total_orders"])} 单)',
                ha='left', va='center', fontsize=9, fontweight='bold',
                color='#1E293B', fontproperties=FONT_PROP)
    ax.set_yticks(range(len(top10)))
    ax.set_yticklabels(top10['merchant_name'], fontproperties=FONT_PROP)
    style_axis(ax)
    ax.set_xlabel('总销售额 (\u00a5)', fontsize=10, color='#64748B', fontproperties=FONT_PROP)
    ax.margins(x=0.25)
    st.pyplot(fig, width='stretch')
    plt.close()


def render_order_status_pie(df_status):
    """渲染订单状态分布环形饼图"""
    status_map = {
        "Paid": ("已支付", "#F59E0B"),
        "Stage1_Assigned": ("干线配送中", "#3B82F6"),
        "Arrived_At_Point": ("已到寄存点", "#8B5CF6"),
        "Stage2_Assigned": ("楼栋配送中", "#06B6D4"),
        "Completed": ("已完成", "#22C55E"),
        "Cancelled": ("已取消", "#EF4444"),
    }
    df_status['display_name'] = df_status['order_status'].map(
        lambda x: status_map.get(x, (x, "#94A3B8"))[0])
    df_status['color'] = df_status['order_status'].map(
        lambda x: status_map.get(x, (x, "#94A3B8"))[1])

    fig, ax = plt.subplots(figsize=(6, 5))
    fig.patch.set_facecolor('none')
    colors_pie = df_status['color'].tolist()
    wedges, texts, autotexts = ax.pie(
        df_status['order_count'],
        labels=df_status['display_name'],
        autopct='%1.1f%%',
        colors=colors_pie,
        startangle=90,
        wedgeprops={'edgecolor': 'white', 'linewidth': 2},
        textprops={'fontsize': 9, 'color': '#1E293B', 'fontproperties': FONT_PROP},
    )
    for at in autotexts:
        at.set_fontweight('bold')
        at.set_fontsize(10)
    centre_circle = plt.Circle((0, 0), 0.50, fc='white', alpha=0.8)
    ax.add_artist(centre_circle)
    ax.text(0, 0, f'{df_status["order_count"].sum()}\n总计',
            ha='center', va='center', fontsize=12, fontweight='bold', color='#1E293B')
    st.pyplot(fig, width='stretch')
    plt.close()


def render_time_period_chart(df_period):
    """渲染时段订单分布柱状图"""
    fig, ax = plt.subplots(figsize=(8, 4))
    fig.patch.set_facecolor('none')
    ax.set_facecolor('none')
    colors_period = ['#F59E0B', '#3B82F6', '#EF4444', '#8B5CF6', '#EF4444', '#06B6D4', '#94A3B8']
    bars = ax.bar(df_period['time_period'], df_period['order_count'],
                  color=colors_period[:len(df_period)], width=0.55,
                  edgecolor='white', linewidth=2, zorder=3)
    for bar, (_, row) in zip(bars, df_period.iterrows()):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f'{int(row["order_count"])}', ha='center', va='bottom',
                fontsize=11, fontweight='bold', color='#1E293B',
                fontproperties=FONT_PROP)
    ax.set_xticks(range(len(df_period)))
    ax.set_xticklabels(df_period['time_period'], fontproperties=FONT_PROP, rotation=15)
    style_axis(ax)
    ax.set_ylabel('订单量', fontsize=10, color='#64748B', fontproperties=FONT_PROP)
    st.pyplot(fig, width='stretch')
    plt.close()


def render_recent_orders_table(df_recent):
    """渲染近期订单流水表格"""
    def style_status(s):
        color_map = {
            'Paid': ('已支付', '#F59E0B'),
            'Stage1_Assigned': ('干线配送中', '#3B82F6'),
            'Arrived_At_Point': ('已到寄存点', '#8B5CF6'),
            'Stage2_Assigned': ('楼栋配送中', '#06B6D4'),
            'Completed': ('已完成', '#22C55E'),
            'Cancelled': ('已取消', '#EF4444'),
        }
        label, color = color_map.get(s, (s, '#94A3B8'))
        return f'<span style="background:{color}20;color:{color};padding:2px 12px;border-radius:20px;font-size:0.8rem;font-weight:500;">{label}</span>'

    html = '<table style="width:100%;border-collapse:collapse;background:white;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.04);">'
    html += '<tr style="background:#F8FAFC;">'
    for col in df_recent.columns:
        html += f'<th style="padding:10px 12px;text-align:left;font-size:0.85rem;color:#64748B;font-weight:600;">{col}</th>'
    html += '</tr>'
    for _, row in df_recent.iterrows():
        html += '<tr style="border-top:1px solid #F1F5F9;">'
        for col in df_recent.columns:
            val = row[col]
            if col == '状态':
                val = style_status(val)
                html += f'<td style="padding:10px 12px;font-size:0.9rem;">{val}</td>'
            elif col == '金额(元)':
                html += f'<td style="padding:10px 12px;font-size:0.9rem;font-weight:600;">\u00a5{val:.2f}</td>'
            else:
                html += f'<td style="padding:10px 12px;font-size:0.9rem;">{val}</td>'
        html += '</tr>'
    html += '</table>'
    st.markdown(html, unsafe_allow_html=True)


# ================================================================
# 页面主程序
# ================================================================

def main():
    # ---- 侧边栏：时间范围过滤器 ----
    with st.sidebar:
        st.markdown("### 筛选条件")
        date_options = ["今天", "最近 7 天", "最近 30 天", "本月", "全部数据"]
        selected_date = st.selectbox(
            "时间范围",
            date_options,
            index=date_options.index(st.session_state.get("date_filter_opt", "全部数据")),
            key="date_filter_opt",
        )
        st.markdown("---")
        st.caption("校园外卖两段式配送数据库系统")
        st.caption(f"数据更新时间: {datetime.now().strftime('%m-%d %H:%M')}")

    # ---- 数据库连接检测 ----
    try:
        stats = load_basic_stats()
    except Exception as e:
        st.error(f"数据库连接失败！请检查 .env 文件中的 MYSQL_PASSWORD 配置。\n\n错误信息: {e}")
        st.info("请确保 .env 文件存在且 MYSQL_PASSWORD 配置正确。")
        return

    # ==================== 头部标题 ====================
    now = datetime.now()
    time_label = st.session_state.get("date_filter_opt", "全部数据")
    st.markdown(f"""
    <div class="header-container">
        <div class="header-title">校园外卖两段式配送 · 实时数据监控大屏</div>
        <div class="header-sub">{now.year}-{now.month:02d}-{now.day:02d} {now:%H:%M:%S} UTC+8 · 数据来源: campus_delivery_db · 筛选: {time_label}</div>
    </div>
    """, unsafe_allow_html=True)

    # ==================== KPI 指标行 ====================
    render_kpi_row(stats)

    st.markdown("<br>", unsafe_allow_html=True)

    # ==================== 新增行：时段订单分布（全宽） ====================
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown('<div class="chart-title">时段订单分布（高峰分析）</div>', unsafe_allow_html=True)
    try:
        df_period = load_time_period_distribution()
        if df_period.empty:
            st.info("暂无订单数据。")
        else:
            render_time_period_chart(df_period)
            # 显示高峰 vs 非高峰对比摘要
            peak_mask = df_period['time_period'].str.contains('高峰|夜宵')
            peak_orders = int(df_period[peak_mask]['order_count'].sum())
            total_orders = int(df_period['order_count'].sum())
            peak_pct = round(peak_orders / total_orders * 100, 1) if total_orders > 0 else 0
            st.markdown(
                f'<div style="text-align:center;color:#64748B;font-size:0.85rem;padding:0.5rem;">'
                f'高峰+夜宵时段订单占比: <strong style="color:#EF4444;font-size:1rem;">{peak_pct}%</strong> '
                f'（{peak_orders} / {total_orders} 单）'
                f'</div>',
                unsafe_allow_html=True
            )
    except Exception as e:
        st.error("加载时段分布数据失败")
        st.code(traceback.format_exc())
    st.markdown('</div>', unsafe_allow_html=True)

    # ==================== 宽屏网格布局 ====================
    # 第一行：左（商户排行）+ 右（运力饼图）
    col_left, col_right = st.columns([1.2, 1])

    with col_left:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown('<div class="chart-title">商户销售排行 Top 10</div>', unsafe_allow_html=True)
        try:
            df_merchants = load_merchant_sales_rank()
            if df_merchants.empty:
                st.info("暂无商户数据。")
            else:
                render_merchant_rank_chart(df_merchants)
        except Exception as e:
            st.error("加载商户排行数据失败")
            st.code(traceback.format_exc())
        st.markdown('</div>', unsafe_allow_html=True)

    with col_right:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown('<div class="chart-title">订单状态分布</div>', unsafe_allow_html=True)
        try:
            df_status = load_order_status_distribution()
            if df_status.empty:
                st.info("暂无订单数据。")
            else:
                render_order_status_pie(df_status)
        except Exception as e:
            st.error("加载订单状态数据失败")
            st.code(traceback.format_exc())
        st.markdown('</div>', unsafe_allow_html=True)

    # 第二行：左（寄存点饱和度）+ 右（近期订单流水）
    col_left2, col_right2 = st.columns([1.2, 1])

    with col_left2:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown('<div class="chart-title">寄存点饱和度监控</div>', unsafe_allow_html=True)
        try:
            df_points = load_pickup_analytics()
            if df_points.empty:
                st.info("暂无寄存点数据。")
            else:
                render_pickup_saturation_chart(df_points)
        except Exception as e:
            st.error("加载寄存点数据失败")
            st.code(traceback.format_exc())
        st.markdown('</div>', unsafe_allow_html=True)

    with col_right2:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown('<div class="chart-title">近期订单流水（最新10条）</div>', unsafe_allow_html=True)
        try:
            df_recent = load_recent_orders(10)
            if df_recent.empty:
                st.info("暂无订单数据。")
            else:
                render_recent_orders_table(df_recent)
        except Exception as e:
            st.error("加载近期订单数据失败")
            st.code(traceback.format_exc())
        st.markdown('</div>', unsafe_allow_html=True)

    # ==================== AI 智能数据助手（全宽） ====================
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown('<div class="chart-title">AI 智能数据助手 (DeepSeek Text-to-SQL)</div>', unsafe_allow_html=True)

    if not DEEPSEEK_API_KEY:
        st.warning("DeepSeek API Key 未配置！请添加到 .env 文件中:\n\n```\nDEEPSEEK_API_KEY=your_api_key\n```")
        st.info("获取 DeepSeek API Key: https://platform.deepseek.com/")
    else:
        st.markdown("""
            <div class="ai-chat-container">
                <div style="font-size:1rem;font-weight:600;margin-bottom:0.5rem;">AI 自然语言数据查询</div>
                <div style="font-size:0.85rem;color:#64748B;margin-bottom:1rem;">
                    输入中文问题，AI 自动转换为 SQL 并返回查询结果表格。
                    例如: "哪个商家销售额最高？" "共有多少学生注册？" "各寄存点饱和度情况"
                </div>
            </div>
            """, unsafe_allow_html=True)

        # 初始化聊天历史
        if "ai_chat_history" not in st.session_state:
            st.session_state.ai_chat_history = []

        # 示例问题快捷按钮
        st.markdown("##### 快捷问题示例")
        example_cols = st.columns(3)
        examples = [
            "哪个商家销售额最高？",
            "共有多少学生注册？",
            "各寄存点饱和度如何？",
        ]
        for i, (col, example) in enumerate(zip(example_cols, examples)):
            with col:
                if st.button(example, key=f"ai_example_{i}", width='stretch'):
                    st.session_state.ai_input = example

        # 用户输入
        user_input = st.text_input(
            "请输入您的问题:",
            key="ai_input",
            placeholder="例如: 哪个商家销售额最高？",
            label_visibility="collapsed",
        )

        col_submit, col_clear = st.columns([1, 5])
        with col_submit:
            submit_clicked = st.button("发送", type="primary", width='stretch')
        with col_clear:
            if st.button("清除记录", width='stretch'):
                st.session_state.ai_chat_history = []
                st.rerun()

        if submit_clicked and user_input:
            with st.spinner("AI 正在思考并生成 SQL..."):
                result = ai_text_to_sql(user_input)

            # 添加到聊天历史
            st.session_state.ai_chat_history.append({
                "role": "user",
                "content": user_input,
            })

            if result["success"]:
                st.session_state.ai_chat_history.append({
                    "role": "assistant",
                    "content": f"查询成功！共找到 {result['row_count']} 条记录",
                    "sql": result["sql"],
                    "result": result["result"],
                    "columns": result["columns"],
                })
            else:
                st.session_state.ai_chat_history.append({
                    "role": "assistant",
                    "content": result["error"],
                    "sql": result.get("sql", ""),
                    "result": [],
                    "columns": [],
                    "is_error": True,
                })

        # 显示聊天历史
        for msg in st.session_state.ai_chat_history:
            if msg["role"] == "user":
                st.markdown(f'<div class="ai-message user"><strong>您:</strong> {msg["content"]}</div>', unsafe_allow_html=True)
            else:
                if msg.get("is_error"):
                    st.markdown(f'<div class="ai-message error"><strong>AI:</strong> {msg["content"]}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="ai-message assistant"><strong>AI:</strong> {msg["content"]}</div>', unsafe_allow_html=True)

                # 显示 SQL
                if msg.get("sql"):
                    st.markdown(f'<div class="ai-message sql"><strong>生成的 SQL:</strong>\n{msg["sql"]}</div>', unsafe_allow_html=True)

                # 显示结果表格
                if msg.get("result") and len(msg["result"]) > 0:
                    df_result = pd.DataFrame(msg["result"])

                    # 表格展示
                    st.dataframe(df_result, width='stretch', hide_index=True)

                    # 自动图表：如果有数值列且行数>1，自动生成柱状图
                    num_cols = df_result.select_dtypes(include=['float64', 'int64']).columns.tolist()
                    if len(num_cols) >= 1 and len(df_result) > 1:
                        with st.expander("查看图表"):
                            chart_tab1, chart_tab2 = st.columns(2)
                            with chart_tab1:
                                st.caption("柱状图（第一列数值）")
                                try:
                                    first_text_col = df_result.select_dtypes(exclude=['float64', 'int64']).columns[0]
                                    st.bar_chart(df_result.set_index(first_text_col)[num_cols[0]], width='stretch')
                                except Exception:
                                    pass
                            with chart_tab2:
                                if len(num_cols) > 1:
                                    st.caption("折线图（前 3 列数值）")
                                    try:
                                        first_text_col = df_result.select_dtypes(exclude=['float64', 'int64']).columns[0]
                                        st.line_chart(df_result.set_index(first_text_col)[num_cols[:3]], width='stretch')
                                    except Exception:
                                        pass

                    # CSV 下载按钮
                    csv_data = df_result.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        label="下载 CSV",
                        data=csv_data,
                        file_name=f"ai_query_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )

    st.markdown('</div>', unsafe_allow_html=True)

    # ---- 页脚 ----
    st.markdown("""
    <div class="footer">
        校园外卖两段式配送数据库系统 · 期末答辩项目 · 基于 Streamlit & MySQL & DeepSeek AI
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
