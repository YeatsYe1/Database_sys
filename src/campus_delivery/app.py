# -*- coding: utf-8 -*-
"""校园外卖两段式配送数据库系统 · 主页面布局"""

import streamlit as st
import pandas as pd
import traceback
from datetime import datetime

from src.campus_delivery.config import GLOBAL_CSS, setup_page
from src.campus_delivery.db import (
    load_pickup_analytics, load_merchant_sales_rank,
    load_order_status_distribution, load_basic_stats,
    load_recent_orders, load_time_period_distribution,
    load_merchant_info, load_student_info, load_merchant_dishes,
    load_rider_info, load_pickup_point_info,
    _get_date_option,
)
from src.campus_delivery.charts import (
    render_kpi_row, render_pickup_saturation_chart,
    render_merchant_rank_chart, render_order_status_pie,
    render_time_period_chart, render_recent_orders_table
)
from src.campus_delivery.ai_assistant import render_ai_assistant


def render_sidebar_details():
    """侧边栏：明细数据表格"""
    with st.sidebar:
        st.markdown("## 明细数据")

        with st.expander("商户信息一览", expanded=False):
            try:
                df = load_merchant_info()
                if df.empty:
                    st.info("暂无商户数据。")
                else:
                    st.dataframe(df, use_container_width=True, hide_index=True)
            except Exception:
                st.error("加载商户信息失败")
                st.code(traceback.format_exc())

        with st.expander("学生用户信息一览", expanded=False):
            try:
                df = load_student_info()
                if df.empty:
                    st.info("暂无学生数据。")
                else:
                    st.dataframe(df, use_container_width=True, hide_index=True)
            except Exception:
                st.error("加载学生信息失败")
                st.code(traceback.format_exc())

        with st.expander("菜品信息一览", expanded=False):
            try:
                df = load_merchant_dishes()
                if df.empty:
                    st.info("暂无菜品数据。")
                else:
                    st.dataframe(df, use_container_width=True, hide_index=True)
            except Exception:
                st.error("加载菜品信息失败")
                st.code(traceback.format_exc())

        st.markdown("---")
        st.markdown("### 骑手信息")
        with st.expander("骑手信息一览", expanded=False):
            try:
                df = load_rider_info()
                if df.empty:
                    st.info("暂无骑手数据。")
                else:
                    st.dataframe(df, use_container_width=True, hide_index=True)
            except Exception:
                st.error("加载骑手信息失败")
                st.code(traceback.format_exc())

        with st.expander("寄存站点信息一览", expanded=False):
            try:
                df = load_pickup_point_info()
                if df.empty:
                    st.info("暂无站点数据。")
                else:
                    st.dataframe(df, use_container_width=True, hide_index=True)
            except Exception:
                st.error("加载站点信息失败")
                st.code(traceback.format_exc())

        st.markdown("---")
        st.caption("校园外卖两段式配送数据库系统")
        st.caption(f"数据更新时间: {datetime.now().strftime('%m-%d %H:%M')}")


def main():
    setup_page()
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

    # ---- 侧边栏 ----
    render_sidebar_details()

    # ---- 顶部标题 ----
    now = datetime.now()
    st.markdown(f"""
    <div class="header-container">
        <div class="header-title">校园外卖两段式配送 · 实时数据监控大屏</div>
        <div class="header-sub">{now.year}-{now.month:02d}-{now.day:02d} {now:%H:%M:%S} UTC+8 · 数据来源: campus_delivery_db</div>
    </div>
    """, unsafe_allow_html=True)

    # ---- 时间范围筛选 ----
    col_filter_label, col_filter_select = st.columns([1, 4])
    with col_filter_label:
        st.markdown('<div style="padding-top:6px;font-weight:600;color:#4F46E5;">时间范围筛选:</div>', unsafe_allow_html=True)
    with col_filter_select:
        date_options = ["今天", "最近 7 天", "最近 30 天", "本月", "全部数据"]
        current_opt = _get_date_option()
        st.selectbox(
            "时间范围", date_options,
            index=date_options.index(current_opt) if current_opt in date_options else 4,
            key="date_filter_opt", label_visibility="collapsed",
        )
    date_option = _get_date_option()

    # ---- 数据库连接检测 ----
    try:
        stats = load_basic_stats(date_option)
    except Exception as e:
        st.error(f"数据库连接失败！请检查 .env 文件中的 MYSQL_PASSWORD 配置。\n\n错误信息: {e}")
        st.info("请确保 .env 文件存在且 MYSQL_PASSWORD 配置正确。")
        return

    # ---- KPI 指标行 ----
    render_kpi_row(stats)
    st.divider()

    # ---- 图表布局 ----
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
        except Exception:
            st.error("加载商户排行数据失败")
            st.code(traceback.format_exc())
        st.markdown('</div>', unsafe_allow_html=True)

    with col_right:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown('<div class="chart-title">订单状态分布</div>', unsafe_allow_html=True)
        try:
            df_status = load_order_status_distribution(date_option)
            if df_status.empty:
                st.info("暂无订单数据。")
            else:
                render_order_status_pie(df_status)
        except Exception:
            st.error("加载订单状态数据失败")
            st.code(traceback.format_exc())
        st.markdown('</div>', unsafe_allow_html=True)

    # ---- 近期订单流水 ----
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown('<div class="chart-title">近期订单流水（最新10条）</div>', unsafe_allow_html=True)
    try:
        df_recent = load_recent_orders(10, date_option)
        if df_recent.empty:
            st.info("暂无订单数据。")
        else:
            render_recent_orders_table(df_recent)
    except Exception:
        st.error("加载近期订单数据失败")
        st.code(traceback.format_exc())
    st.markdown('</div>', unsafe_allow_html=True)

    # ---- 寄存点饱和度监控 ----
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown('<div class="chart-title">寄存点饱和度监控</div>', unsafe_allow_html=True)
    try:
        df_points = load_pickup_analytics()
        if df_points.empty:
            st.info("暂无寄存点数据。")
        else:
            df_points['point_name'] = df_points['point_name'].str.replace('智能寄存柜', '', regex=False).str.strip()
            render_pickup_saturation_chart(df_points)
    except Exception:
        st.error("加载寄存点数据失败")
        st.code(traceback.format_exc())
    st.markdown('</div>', unsafe_allow_html=True)

    st.divider()

    # ---- 时段订单分布 ----
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown('<div class="chart-title">时段订单分布（高峰分析）</div>', unsafe_allow_html=True)
    try:
        df_period = load_time_period_distribution(date_option)
        if df_period.empty:
            st.info("暂无订单数据。")
        else:
            render_time_period_chart(df_period)
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
    except Exception:
        st.error("加载时段分布数据失败")
        st.code(traceback.format_exc())
    st.markdown('</div>', unsafe_allow_html=True)

    st.divider()

    # ---- AI 智能数据助手 ----
    render_ai_assistant()

    # ---- 页脚 ----
    st.markdown("""
    <div class="footer">
        校园外卖两段式配送数据库系统 · 期末答辩项目 · 基于 Streamlit & MySQL & DeepSeek AI
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
