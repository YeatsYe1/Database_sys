# -*- coding: utf-8 -*-
"""
==================================================================
项目名称：校园外卖两段式配送数据库系统 (campus_delivery_db)
文件名称：dashboard_app.py
功能描述：Streamlit 精美数据可视化大屏（期末答辩展示）
设计风格：现代简洁 · 卡片化 · 渐变色 · 深色/浅色自适应
适用环境：Python 3.8+ / streamlit / pymysql / pandas / matplotlib
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
from datetime import datetime
import os
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# ---------------------------------------------------------------
# Matplotlib 中文字体配置 - 直接指定系统字体文件路径
# ---------------------------------------------------------------
plt.rcParams['axes.unicode_minus'] = False

# Windows 系统中文字体候选物理路径
_CHINESE_FONT_PATHS = [
    r"C:\Windows\Fonts\msyh.ttc",      # Microsoft YaHei 常规
    r"C:\Windows\Fonts\msyhbd.ttc",    # Microsoft YaHei 粗体
    r"C:\Windows\Fonts\simhei.ttf",    # SimHei
    r"C:\Windows\Fonts\msyh.ttf",      # Microsoft YaHei (备选)
    r"C:\Windows\Fonts\SIMHEI.TTF",    # SimHei (备选)
]

# 找到第一个存在的字体文件
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
# ⚠️ 数据库连接配置 — 请在此处修改为你的 MySQL 密码
# ================================================================
DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD"),
    "database": os.getenv("MYSQL_DATABASE", "campus_delivery_db"),
    "charset": os.getenv("MYSQL_CHARSET", "utf8mb4"),
    "use_unicode": True,
    "init_command": "SET NAMES utf8mb4",
}

# ---- 页面路径 ----
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ---- 全局配色方案 ----
COLOR_PRIMARY = "#4F46E5"      # 靛蓝
COLOR_SECONDARY = "#06B6D4"    # 青色
COLOR_SUCCESS = "#22C55E"      # 绿色
COLOR_WARNING = "#F59E0B"      # 琥珀
COLOR_DANGER = "#EF4444"       # 红色
COLOR_BG = "#F8FAFC"           # 浅灰背景
COLOR_CARD = "#FFFFFF"         # 卡片白色
COLOR_TEXT = "#1E293B"         # 深色文字

# ---- Streamlit 页面配置 ----
st.set_page_config(
    page_title="校园外卖两段式配送 · 实时数据监控大屏",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---- 自定义全局 CSS ----
st.markdown(f"""
<style>
    /* 全局样式 */
    .stApp {{
        background: {COLOR_BG};
        font-family: "Microsoft YaHei", "SimHei", "Arial Unicode MS", "Noto Sans CJK SC", sans-serif;
    }}
    body, .stApp, .css-1v0mbdj, .css-18ni7ap {{
        font-family: "Microsoft YaHei", "SimHei", "Arial Unicode MS", "Noto Sans CJK SC", sans-serif;
    }}
    /* 标题区域 */
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
    /* 指标卡片 */
    .metric-card {{
        background: {COLOR_CARD};
        padding: 1.2rem 1rem;
        border-radius: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        text-align: center;
        border-left: 4px solid {COLOR_PRIMARY};
        transition: transform 0.2s;
    }}
    .metric-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 16px rgba(0,0,0,0.1);
    }}
    .metric-value {{
        font-size: 1.8rem;
        font-weight: 700;
        color: {COLOR_PRIMARY};
    }}
    .metric-label {{
        font-size: 0.85rem;
        color: #64748B;
        margin-top: 0.2rem;
    }}
    /* 区块标题 */
    .section-title {{
        font-size: 1.3rem;
        font-weight: 600;
        color: {COLOR_TEXT};
        margin: 1rem 0 0.8rem;
        padding-left: 0.8rem;
        border-left: 4px solid {COLOR_PRIMARY};
    }}
    /* 页脚 */
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

@st.cache_data(ttl=60)
def load_pickup_analytics():
    """读取寄存点饱和度分析"""
    conn = pymysql.connect(**DB_CONFIG)
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
    conn = pymysql.connect(**DB_CONFIG)
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
    conn = pymysql.connect(**DB_CONFIG)
    try:
        query = """
            SELECT order_status, COUNT(*) AS order_count
            FROM orders
            GROUP BY order_status
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
    conn = pymysql.connect(**DB_CONFIG)
    try:
        stats = {}
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM users")
            stats["总用户数"] = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM merchants")
            stats["总商家数"] = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM orders")
            stats["总订单数"] = cursor.fetchone()[0]
            cursor.execute("SELECT IFNULL(SUM(total_amount), 0) FROM orders WHERE order_status = 'Completed'")
            stats["总营业额"] = cursor.fetchone()[0]
        return stats
    finally:
        conn.close()

@st.cache_data(ttl=60)
def load_recent_orders(limit=10):
    """读取最近订单"""
    conn = pymysql.connect(**DB_CONFIG)
    try:
        query = f"""
            SELECT 
                o.order_id AS '订单号',
                u.username AS '学生',
                m.merchant_name AS '商家',
                o.total_amount AS '金额(元)',
                o.order_status AS '状态',
                DATE_FORMAT(o.created_at, '%m-%d %H:%i') AS '下单时间'
            FROM orders o
            JOIN users u ON o.user_id = u.user_id
            JOIN merchants m ON o.merchant_id = m.merchant_id
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

# ================================================================
# 页面主程序
# ================================================================

def main():
    # ---- 数据库连接检测 ----
    try:
        stats = load_basic_stats()
    except Exception as e:
        st.error(f"❌ 数据库连接失败！请检查 MySQL 密码配置。\n\n错误详情: {e}")
        st.info("💡 请在 dashboard_app.py 中找到 DB_CONFIG，修改 password 为你实际的 MySQL 密码。")
        return

    # ==================== 头部标题 ====================
    now = datetime.now()
    st.markdown(f"""
    <div class="header-container">
        <div class="header-title">🚀 校园外卖两段式配送 · 实时数据监控大屏</div>
        <div class="header-sub">📅 {now.year}年{now.month}月{now.day}日 {now:%H:%M:%S} 更新 · 数据源自 campus_delivery_db</div>
    </div>
    """, unsafe_allow_html=True)

    # ==================== KPI 指标行 ====================
    col1, col2, col3, col4 = st.columns(4)
    kpi_data = [
        ("👥 注册学生", f"{int(stats['总用户数'])} 人", COLOR_PRIMARY),
        ("🏪 入驻商家", f"{int(stats['总商家数'])} 家", COLOR_SECONDARY),
        ("📦 历史订单", f"{int(stats['总订单数'])} 单", COLOR_SUCCESS),
        ("💰 总营业额", f"¥{float(stats['总营业额']):,.2f}", COLOR_WARNING),
    ]
    for col, (label, value, color) in zip([col1, col2, col3, col4], kpi_data):
        with col:
            st.markdown(f"""
            <div class="metric-card" style="border-left-color: {color};">
                <div class="metric-value" style="color: {color};">{value}</div>
                <div class="metric-label">{label}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ==================== Tab 布局 ====================
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 寄存柜饱和度预警",
        "🏆 商户销售排行榜",
        "🛵 两段式运力监控",
        "📋 近期订单流水",
    ])

    # --------------------------------------------------
    # TAB 1：寄存柜饱和度预警
    # --------------------------------------------------
    with tab1:
        st.markdown('<div class="section-title">📊 寄存点容量饱和度监控</div>', unsafe_allow_html=True)

        try:
            df_points = load_pickup_analytics()
            if df_points.empty:
                st.info("📭 暂无寄存点数据。")
            else:
                col_chart, col_info = st.columns([2, 1])

                with col_chart:
                    fig, ax = plt.subplots(figsize=(10, 4.5))
                    fig.patch.set_facecolor('none')
                    ax.set_facecolor('none')

                    names = df_points['point_name'].tolist()
                    values = df_points['saturation_pct'].tolist()
                    colors_bar = ['#22C55E' if v < 60 else '#F59E0B' if v < 80 else '#EF4444' for v in values]

                    bars = ax.bar(names, values, color=colors_bar, width=0.5,
                                  edgecolor='white', linewidth=2, zorder=3)
                    ax.axhline(y=80, color='#EF4444', linestyle='--', linewidth=1.5,
                               alpha=0.7, label='⚠️ 爆仓警戒线 80%', zorder=2)
                    ax.axhline(y=60, color='#F59E0B', linestyle='--', linewidth=1,
                               alpha=0.5, label='⚠️ 注意警戒线 60%', zorder=2)

                    for bar, v in zip(bars, values):
                        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
                                f'{v:.1f}%', ha='center', va='bottom',
                                fontsize=13, fontweight='bold', color='#1E293B',
                                fontproperties=FONT_PROP)

                    ax.set_xticks(range(len(names)))
                    ax.set_xticklabels(names, fontproperties=FONT_PROP)
                    ax.set_ylim(0, 105)
                    style_axis(ax)
                    ax.legend(fontsize=9, loc='upper right', framealpha=0.8, prop=FONT_PROP)
                    ax.set_ylabel('饱和度 (%)', fontsize=11, color='#64748B', fontproperties=FONT_PROP)
                    st.pyplot(fig, use_container_width=True)
                    plt.close()

                with col_info:
                    for _, row in df_points.iterrows():
                        sat = row['saturation_pct']
                        bg_color = '#FEF2F2' if sat > 80 else '#FFFBEB' if sat > 60 else '#F0FDF4'
                        border = '#EF4444' if sat > 80 else '#F59E0B' if sat > 60 else '#22C55E'
                        icon = '🚨' if sat > 80 else '⚠️' if sat > 60 else '✅'

                        st.markdown(f"""
                        <div style="background:{bg_color};padding:1rem;border-radius:12px;
                                    border-left:4px solid {border};margin-bottom:0.8rem;">
                            <div style="font-size:1.1rem;font-weight:600;">{icon} {row['point_name']}</div>
                            <div style="font-size:1.3rem;font-weight:700;color:{border};margin:0.3rem 0;">
                                饱和度 {sat:.1f}%
                            </div>
                            <div style="color:#64748B;font-size:0.85rem;">
                                在库 {int(row['current_packages'])} / 最大 {int(row['max_capacity'])} 格 · 积压待取 {int(row['backlog_count'])} 件
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"❌ 加载寄存点数据失败")
            import traceback
            st.code(traceback.format_exc())

    # --------------------------------------------------
    # TAB 2：商户销售排行榜
    # --------------------------------------------------
    with tab2:
        st.markdown('<div class="section-title">🏆 校园商户销售排行榜 Top 10</div>', unsafe_allow_html=True)

        try:
            df_merchants = load_merchant_sales_rank()
            if df_merchants.empty:
                st.info("📭 暂无商户数据。")
            else:
                top10 = df_merchants.head(10).iloc[::-1]  # 反转

                col_chart, col_table = st.columns([2, 1])

                with col_chart:
                    fig, ax = plt.subplots(figsize=(10, 6))
                    fig.patch.set_facecolor('none')
                    ax.set_facecolor('none')

                    palette = sns.color_palette("viridis", len(top10))[::-1]
                    bars = ax.barh(top10['merchant_name'], top10['total_sales'],
                                   color=palette, edgecolor='white', linewidth=1.5, height=0.6, zorder=3)

                    for bar, (_, row) in zip(bars, top10.iterrows()):
                        w = bar.get_width()
                        ax.text(w + 10, bar.get_y() + bar.get_height()/2,
                                f'¥{w:,.0f}  ({int(row["total_orders"])}单)',
                                ha='left', va='center', fontsize=10, fontweight='bold',
                                color='#1E293B', fontproperties=FONT_PROP)

                    # 设置 Y 轴标签字体
                    ax.set_yticklabels(top10['merchant_name'], fontproperties=FONT_PROP)
                    style_axis(ax)
                    ax.set_xlabel('累计销售总额 (元)', fontsize=11, color='#64748B', fontproperties=FONT_PROP)
                    ax.margins(x=0.25)
                    st.pyplot(fig, use_container_width=True)
                    plt.close()

                with col_table:
                    display_df = top10[['sales_rank', 'merchant_name', 'total_orders', 'total_sales']].copy()
                    display_df.columns = ['排名', '商户名称', '成功单数', '累计销售额']
                    display_df['累计销售额'] = display_df['累计销售额'].apply(lambda x: f"¥{x:,.2f}")
                    display_df.index = range(1, len(display_df)+1)
                    st.dataframe(display_df, use_container_width=True, height=400)

        except Exception as e:
            st.error(f"❌ 加载商户排行失败")
            import traceback
            st.code(traceback.format_exc())

    # --------------------------------------------------
    # TAB 3：运力状态监控
    # --------------------------------------------------
    with tab3:
        st.markdown('<div class="section-title">🛵 两段式运力状态流转</div>', unsafe_allow_html=True)

        try:
            df_status = load_order_status_distribution()
            if df_status.empty:
                st.info("📭 暂无订单数据。")
            else:
                status_map = {
                    "Paid": ("⏳ 已支付", "#F59E0B"),
                    "Stage1_Assigned": ("🚚 干线配送", "#3B82F6"),
                    "Arrived_At_Point": ("📦 到寄存点", "#8B5CF6"),
                    "Stage2_Assigned": ("🛵 楼栋配送", "#06B6D4"),
                    "Completed": ("✅ 已完成", "#22C55E"),
                    "Cancelled": ("❌ 已取消", "#EF4444"),
                }
                df_status['显示名称'] = df_status['order_status'].map(
                    lambda x: status_map.get(x, (x, "#94A3B8"))[0])
                df_status['颜色'] = df_status['order_status'].map(
                    lambda x: status_map.get(x, (x, "#94A3B8"))[1])

                col1, col2 = st.columns([1.3, 1])

                with col1:
                    fig, ax = plt.subplots(figsize=(7, 5))
                    fig.patch.set_facecolor('none')

                    colors_pie = df_status['颜色'].tolist()
                    wedges, texts, autotexts = ax.pie(
                        df_status['order_count'],
                        labels=df_status['显示名称'],
                        autopct='%1.1f%%',
                        colors=colors_pie,
                        startangle=90,
                        wedgeprops={'edgecolor': 'white', 'linewidth': 2},
                        textprops={'fontsize': 10, 'color': '#1E293B', 'fontproperties': FONT_PROP},
                    )
                    for at in autotexts:
                        at.set_fontweight('bold')
                        at.set_fontsize(11)

                    centre_circle = plt.Circle((0, 0), 0.50, fc='white', alpha=0.8)
                    ax.add_artist(centre_circle)
                    ax.text(0, 0, f'{df_status["order_count"].sum()}\n总订单',
                            ha='center', va='center', fontsize=13, fontweight='bold', color='#1E293B')
                    st.pyplot(fig, use_container_width=True)
                    plt.close()

                with col2:
                    total = df_status['order_count'].sum()
                    completed = df_status[df_status['order_status'] == 'Completed']['order_count'].sum() \
                        if 'Completed' in df_status['order_status'].values else 0
                    completion_rate = completed / total * 100 if total > 0 else 0

                    st.markdown("""
                    <div style="background:white;border-radius:16px;padding:1.5rem;box-shadow:0 2px 8px rgba(0,0,0,0.04);">
                        <div style="font-size:1rem;font-weight:600;margin-bottom:1rem;">📊 运力健康度</div>
                    """, unsafe_allow_html=True)

                    for _, row in df_status.iterrows():
                        pct = row['order_count'] / total * 100
                        st.markdown(f"""
                        <div style="display:flex;align-items:center;margin-bottom:0.6rem;">
                            <div style="width:100px;font-size:0.85rem;color:#64748B;">{row['显示名称']}</div>
                            <div style="flex:1;background:#F1F5F9;border-radius:8px;height:8px;margin:0 10px;">
                                <div style="background:{row['颜色']};width:{pct}%;height:8px;border-radius:8px;"></div>
                            </div>
                            <div style="font-size:0.85rem;font-weight:600;min-width:50px;text-align:right;">
                                {int(row['order_count'])} ({pct:.1f}%)
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                    st.markdown(f"""
                        <hr style="margin:1rem 0;border-color:#E2E8F0;">
                        <div style="display:flex;justify-content:space-between;">
                            <span style="color:#64748B;">✅ 完成率</span>
                            <span style="font-weight:700;color:#22C55E;">{completion_rate:.1f}%</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"❌ 加载运力状态数据失败")
            import traceback
            st.code(traceback.format_exc())

    # --------------------------------------------------
    # TAB 4：近期订单流水
    # --------------------------------------------------
    with tab4:
        st.markdown('<div class="section-title">📋 近期订单流水</div>', unsafe_allow_html=True)

        try:
            df_recent = load_recent_orders(10)
            if df_recent.empty:
                st.info("📭 暂无订单数据。")
            else:
                def style_status(s):
                    color_map = {
                        'Paid': ('⏳ 已支付', '#F59E0B'),
                        'Stage1_Assigned': ('🚚 干线配送', '#3B82F6'),
                        'Arrived_At_Point': ('📦 到寄存点', '#8B5CF6'),
                        'Stage2_Assigned': ('🛵 楼栋配送', '#06B6D4'),
                        'Completed': ('✅ 已完成', '#22C55E'),
                        'Cancelled': ('❌ 已取消', '#EF4444'),
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
                            html += f'<td style="padding:10px 12px;font-size:0.9rem;font-weight:600;">¥{val:.2f}</td>'
                        else:
                            html += f'<td style="padding:10px 12px;font-size:0.9rem;">{val}</td>'
                    html += '</tr>'
                html += '</table>'
                st.markdown(html, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"❌ 加载订单流水失败")
            import traceback
            st.code(traceback.format_exc())

    # ---- 页脚 ----
    st.markdown("""
    <div class="footer">
        🏫 校园外卖两段式配送数据库系统 · 期末答辩展示 · Powered by Streamlit & MySQL
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
