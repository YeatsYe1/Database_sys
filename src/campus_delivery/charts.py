# -*- coding: utf-8 -*-
"""Matplotlib 图表渲染模块"""

import streamlit as st
import pandas as pd
import os
import sys
import io

if sys.platform == "win32":
    try:
        if sys.stdout.buffer and not sys.stdout.buffer.closed:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        if sys.stderr.buffer and not sys.stderr.buffer.closed:
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
    except Exception:
        pass

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns

from src.campus_delivery.config import (
    COLOR_PRIMARY, COLOR_SECONDARY, COLOR_SUCCESS,
    COLOR_WARNING, COLOR_DANGER, COLOR_TEXT
)

# ---- 中文字体配置 ----
plt.rcParams['axes.unicode_minus'] = False

def _setup_chinese_font():
    try:
        fm._load_fontmanager(try_read_cache=False)
    except Exception:
        pass

    _font_dirs = [
        r"C:\Windows\Fonts", r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\msyhbd.ttc", r"C:\Windows\Fonts\simhei.ttf",
        r"C:\Windows\Fonts\msyh.ttf", r"C:\Windows\Fonts\SIMHEI.TTF",
        r"C:\Windows\Fonts\simsun.ttc", r"C:\Windows\Fonts\SIMYOU.TTF",
    ]
    for _d in _font_dirs:
        if os.path.isdir(_d):
            for _f in fm.findSystemFonts(fontpaths=[_d]):
                try:
                    fm.fontManager.addfont(_f)
                except Exception:
                    pass
        elif os.path.isfile(_d):
            try:
                fm.fontManager.addfont(_d)
            except Exception:
                pass

    _candidate_families = [
        "Microsoft YaHei", "SimHei", "Noto Sans SC",
        "Noto Sans CJK SC", "WenQuanYi Micro Hei", "SimSun",
        "KaiTi", "FangSong", "Arial Unicode MS",
    ]
    _found_family = None
    for _fam in _candidate_families:
        try:
            _fp = fm.FontProperties(family=_fam)
            _test_path = fm.findfont(_fp, fallback_to_default=False)
            if _test_path and os.path.exists(_test_path):
                _found_family = _fam
                break
        except Exception:
            continue

    if _found_family is None:
        for _f in fm.fontManager.ttflist:
            if _f.name in _candidate_families:
                _found_family = _f.name
                break

    if _found_family:
        plt.rcParams['font.sans-serif'] = [_found_family, 'DejaVu Sans', 'Arial']
        plt.rcParams['font.family'] = 'sans-serif'
        return fm.FontProperties(family=_found_family)
    else:
        for _p in _font_dirs:
            if os.path.isfile(_p):
                try:
                    _fp = fm.FontProperties(fname=_p)
                    _name = _fp.get_name()
                    plt.rcParams['font.sans-serif'] = [_name, 'DejaVu Sans']
                    plt.rcParams['font.family'] = 'sans-serif'
                    return _fp
                except Exception:
                    continue
        return fm.FontProperties()

FONT_PROP = _setup_chinese_font()


def style_axis(ax):
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#E2E8F0')
    ax.spines['bottom'].set_color('#E2E8F0')
    ax.tick_params(colors='#64748B', labelsize=10)


def render_kpi_row(stats):
    kpi_items = [
        ("总订单量", f"{int(stats['total_orders'])} 单", COLOR_PRIMARY),
        ("活跃商家", f"{int(stats['total_merchants'])} 家", COLOR_SECONDARY),
        ("在途骑手", f"{int(stats['active_riders'])} 人", COLOR_WARNING),
        ("总营业额", f"¥{float(stats['total_revenue']):,.2f}", COLOR_SUCCESS),
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
    fig, ax = plt.subplots(figsize=(8, 4))
    fig.patch.set_facecolor('none')
    ax.set_facecolor('none')
    names = df_points['point_name'].tolist()
    values = df_points['saturation_pct'].tolist()
    colors_bar = ['#22C55E' if v < 60 else '#F59E0B' if v < 80 else '#EF4444' for v in values]
    bars = ax.bar(names, values, color=colors_bar, width=0.5,
                  edgecolor='white', linewidth=2, zorder=3)
    ax.axhline(y=80, color='#EF4444', linestyle='--', linewidth=1.5, alpha=0.7, label='爆仓阈值 80%', zorder=2)
    ax.axhline(y=60, color='#F59E0B', linestyle='--', linewidth=1, alpha=0.5, label='预警阈值 60%', zorder=2)
    for bar, v in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
                f'{v:.1f}%', ha='center', va='bottom',
                fontsize=11, fontweight='bold', color='#1E293B', fontproperties=FONT_PROP)
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, fontproperties=FONT_PROP)
    ax.set_ylim(0, 105)
    style_axis(ax)
    ax.legend(fontsize=9, loc='upper right', framealpha=0.8, prop=FONT_PROP)
    ax.set_ylabel('饱和度 (%)', fontsize=10, color='#64748B', fontproperties=FONT_PROP)
    st.pyplot(fig, use_container_width=True)
    plt.close()

    overflow_points = df_points[df_points['saturation_pct'] > 80]
    if not overflow_points.empty:
        for _, row in overflow_points.iterrows():
            st.warning(
                f"⚠️ 爆仓预警: {row['point_name']} 饱和度 {row['saturation_pct']:.1f}% "
                f"(已用 {int(row['current_packages'])} / 最大 {int(row['max_capacity'])} 格, "
                f"滞留 {int(row['backlog_count'])} 件)"
            )


def render_merchant_rank_chart(df_merchants):
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
                f'¥{w:,.0f}  ({int(row["total_orders"])} 单)',
                ha='left', va='center', fontsize=9, fontweight='bold',
                color='#1E293B', fontproperties=FONT_PROP)
    ax.set_yticks(range(len(top10)))
    ax.set_yticklabels(top10['merchant_name'], fontproperties=FONT_PROP)
    style_axis(ax)
    ax.set_xlabel('总销售额 (¥)', fontsize=10, color='#64748B', fontproperties=FONT_PROP)
    ax.margins(x=0.25)
    st.pyplot(fig, use_container_width=True)
    plt.close()


def render_order_status_pie(df_status):
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
        df_status['order_count'], labels=df_status['display_name'],
        autopct='%1.1f%%', colors=colors_pie, startangle=90,
        wedgeprops={'edgecolor': 'white', 'linewidth': 2},
        textprops={'fontsize': 9, 'color': '#1E293B', 'fontproperties': FONT_PROP},
    )
    for at in autotexts:
        at.set_fontweight('bold')
        at.set_fontsize(10)
    centre_circle = plt.Circle((0, 0), 0.50, fc='white', alpha=0.8)
    ax.add_artist(centre_circle)
    ax.text(0, 0, f'{df_status["order_count"].sum()}\n总计',
            ha='center', va='center', fontsize=12, fontweight='bold', color='#1E293B',
            fontproperties=FONT_PROP)
    st.pyplot(fig, use_container_width=True)
    plt.close()


def render_time_period_chart(df_period):
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
                fontsize=11, fontweight='bold', color='#1E293B', fontproperties=FONT_PROP)
    ax.set_xticks(range(len(df_period)))
    ax.set_xticklabels(df_period['time_period'], fontproperties=FONT_PROP, rotation=45, ha='right')
    style_axis(ax)
    ax.set_ylabel('订单量', fontsize=10, color='#64748B', fontproperties=FONT_PROP)
    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close()


def render_recent_orders_table(df_recent):
    import html as _html

    def _escape_html(val):
        return _html.escape(str(val))

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
        return f'<span style="background:{color}20;color:{color};padding:2px 12px;border-radius:20px;font-size:0.8rem;font-weight:500;">{_escape_html(label)}</span>'

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
