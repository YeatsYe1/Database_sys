# -*- coding: utf-8 -*-
"""配置常量：配色、CSS、页面设置、数据库 Schema 描述"""

import streamlit as st

# ---- 全局配色 ----
COLOR_PRIMARY = "#4F46E5"
COLOR_SECONDARY = "#06B6D4"
COLOR_SUCCESS = "#22C55E"
COLOR_WARNING = "#F59E0B"
COLOR_DANGER = "#EF4444"
COLOR_BG = "#F8FAFC"
COLOR_CARD = "#FFFFFF"
COLOR_TEXT = "#1E293B"

def setup_page():
    st.set_page_config(
        page_title="校园外卖两段式配送 · 实时数据监控大屏",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

GLOBAL_CSS = f"""
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
"""

DB_SCHEMA_DESCRIPTION = """
数据库名称：campus_delivery_db（校园外卖两段式配送系统）

表结构说明：

1. users（学生用户表）
   - user_id: 学生唯一ID (INT, PK)
   - username: 姓名 (VARCHAR)
   - phone: 手机号 (VARCHAR)
   - dorm_building: 宿舍楼栋 (VARCHAR)
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

6. orders（订单主表）
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
"""
