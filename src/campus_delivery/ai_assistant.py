# -*- coding: utf-8 -*-
"""AI 智能数据助手 — DeepSeek Text-to-SQL"""

import streamlit as st
import pandas as pd
import os
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

from src.campus_delivery.config import DB_SCHEMA_DESCRIPTION
from src.campus_delivery.db import get_connection

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")


def init_deepseek_client():
    if not DEEPSEEK_API_KEY:
        return None
    return OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL, timeout=10)


def ai_text_to_sql(user_question: str) -> dict:
    client = init_deepseek_client()
    if not client:
        return {
            "success": False, "sql": "", "result": [],
            "error": "DeepSeek API Key 未配置！请在 .env 文件中设置 DEEPSEEK_API_KEY"
        }

    system_prompt = f"""你是一个专业的 Text-to-SQL 助手。将用户的中文问题转换为 MySQL SQL 查询语句。

数据库 Schema：
{DB_SCHEMA_DESCRIPTION}

要求：
1. 只生成 SELECT 查询语句，绝不生成 INSERT/UPDATE/DELETE/DROP/ALTER 等修改语句
2. 给字段起中文别名（使用 AS）
3. 涉及金额统计时，只统计 order_status='Completed' 的已完成订单
4. 只返回 SQL 语句本身，不要加任何解释或 markdown 标记
5. SQL 语句要兼容 MySQL 8.0 语法"""

    try:
        response = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_question}
            ],
            temperature=0.1, max_tokens=1000, timeout=10,
        )
        sql = response.choices[0].message.content.strip()
        sql = sql.replace("```sql", "").replace("```", "").strip()

        sql_upper = sql.upper().strip()
        if not sql_upper.startswith("SELECT"):
            return {"success": False, "sql": sql, "result": [],
                    "error": "AI 生成的不是查询语句，已拦截执行"}

        dangerous_keywords = [
            "INSERT ", "UPDATE ", "DELETE ", "DROP ", "ALTER ",
            "TRUNCATE ", "CREATE ", "EXEC ", "SHUTDOWN", "INTO OUTFILE",
            "INTO DUMPFILE", "LOAD DATA", "SET @", "@@",
        ]
        for kw in dangerous_keywords:
            if kw in sql_upper:
                return {"success": False, "sql": sql, "result": [],
                        "error": f"检测到危险关键字 '{kw.strip()}'，已拦截执行"}

        if ";" in sql.rstrip(";"):
            return {"success": False, "sql": sql, "result": [],
                    "error": "检测到多条 SQL 语句（含分号），已拦截执行"}

        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
            df = pd.DataFrame(rows, columns=columns)
            result = df.to_dict(orient="records")
            return {"success": True, "sql": sql, "result": result,
                    "columns": columns, "row_count": len(result), "error": ""}
        except Exception as e:
            return {"success": False, "sql": sql, "result": [],
                    "error": f"SQL 执行错误：{str(e)}"}
        finally:
            conn.close()
    except Exception as e:
        return {"success": False, "sql": "", "result": [],
                "error": f"AI 调用失败：{str(e)}"}


def render_ai_assistant():
    """渲染 AI 智能数据助手界面"""
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
    st.markdown('</div>', unsafe_allow_html=True)

    if "ai_chat_history" not in st.session_state:
        st.session_state.ai_chat_history = []

    st.markdown("##### 快捷问题示例")
    example_cols = st.columns(3)
    examples = ["哪个商家销售额最高？", "共有多少学生注册？", "各寄存点饱和度如何？"]
    for i, (col, example) in enumerate(zip(example_cols, examples)):
        with col:
            if st.button(example, key=f"ai_example_{i}", use_container_width=True):
                st.session_state.ai_input = example

    user_input = st.text_input(
        "请输入您的问题:", key="ai_input",
        placeholder="例如: 哪个商家销售额最高？", label_visibility="collapsed",
    )

    col_submit, col_clear = st.columns([1, 5])
    with col_submit:
        submit_clicked = st.button("发送", type="primary", use_container_width=True)
    with col_clear:
        if st.button("清除记录", use_container_width=True):
            st.session_state.ai_chat_history = []
            st.rerun()

    if submit_clicked and user_input:
        with st.spinner("AI 正在思考并生成 SQL..."):
            result = ai_text_to_sql(user_input)

        st.session_state.ai_chat_history.append({"role": "user", "content": user_input})

        if result["success"]:
            st.session_state.ai_chat_history.append({
                "role": "assistant",
                "content": f"查询成功！共找到 {result['row_count']} 条记录",
                "sql": result["sql"], "result": result["result"], "columns": result["columns"],
            })
        else:
            st.session_state.ai_chat_history.append({
                "role": "assistant", "content": result["error"],
                "sql": result.get("sql", ""), "result": [], "columns": [], "is_error": True,
            })

    for msg in st.session_state.ai_chat_history:
        if msg["role"] == "user":
            st.markdown(f'<div class="ai-message user"><strong>您:</strong> {msg["content"]}</div>', unsafe_allow_html=True)
        else:
            if msg.get("is_error"):
                st.markdown(f'<div class="ai-message error"><strong>AI:</strong> {msg["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="ai-message assistant"><strong>AI:</strong> {msg["content"]}</div>', unsafe_allow_html=True)
            if msg.get("sql"):
                st.markdown(f'<div class="ai-message sql"><strong>生成的 SQL:</strong>\n{msg["sql"]}</div>', unsafe_allow_html=True)
            if msg.get("result") and len(msg["result"]) > 0:
                df_result = pd.DataFrame(msg["result"])
                st.dataframe(df_result, use_container_width=True, hide_index=True)
                num_cols = df_result.select_dtypes(include=['float64', 'int64']).columns.tolist()
                if len(num_cols) >= 1 and len(df_result) > 1:
                    with st.expander("查看图表"):
                        chart_tab1, chart_tab2 = st.columns(2)
                        with chart_tab1:
                            st.caption("柱状图（第一列数值）")
                            try:
                                first_text_col = df_result.select_dtypes(exclude=['float64', 'int64']).columns[0]
                                st.bar_chart(df_result.set_index(first_text_col)[num_cols[0]], use_container_width=True)
                            except Exception:
                                pass
                        with chart_tab2:
                            if len(num_cols) > 1:
                                st.caption("折线图（前 3 列数值）")
                                try:
                                    first_text_col = df_result.select_dtypes(exclude=['float64', 'int64']).columns[0]
                                    st.line_chart(df_result.set_index(first_text_col)[num_cols[:3]], use_container_width=True)
                                except Exception:
                                    pass
                csv_data = df_result.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="下载 CSV", data=csv_data,
                    file_name=f"ai_query_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv", use_container_width=True,
                )
