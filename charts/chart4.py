# anudesh_dashboard/charts/chart4.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils import apply_time_filter
import datetime as dt

def render_chart4(conn):
    st.markdown("---")
    st.markdown("### <a name='chart-4'></a>📈 Chart 4: Task Status by Target Language ", unsafe_allow_html=True)

    languages = ["All"] + pd.read_sql(
        "SELECT DISTINCT language FROM intermediate_table WHERE language IS NOT NULL ORDER BY language", 
        conn
    )["language"].tolist()

    statuses = ["annotated", "reviewed", "super_checked", "exported"]

    col1, col2 = st.columns(2)
    with col1:
        selected_language = st.selectbox("🌐 Select Target Language", languages, key="chart4_lang")
    with col2:
        selected_statuses = st.multiselect("✅ Select Task Statuses", statuses, default=statuses, key="chart4_status")

    # Time Filter
    time_filter = st.radio("⏱ Time Range", 
        ["All Time", "Today", "Yesterday", "Last Week", "Last Month", "Custom Range"], 
        horizontal=True, key="chart4_time"
    )

    today = dt.date.today()
    start_date, end_date = None, today

    if time_filter == "Today":
        start_date = today
    elif time_filter == "Yesterday":
        start_date = today - dt.timedelta(days=1)
        end_date = start_date
    elif time_filter == "Last Week":
        start_date = today - dt.timedelta(days=today.weekday() + 7)
        end_date = start_date + dt.timedelta(days=6)
    elif time_filter == "Last Month":
        first_day_this_month = today.replace(day=1)
        start_date = (first_day_this_month - dt.timedelta(days=1)).replace(day=1)
        end_date = first_day_this_month - dt.timedelta(days=1)
    elif time_filter == "Custom Range":
        col3, col4 = st.columns(2)
        with col3:
            start_date = st.date_input("Start Date", value=today - dt.timedelta(days=30), key="chart4_start")
        with col4:
            end_date = st.date_input("End Date", value=today, key="chart4_end")

    where_clauses = []
    params = []

    if selected_language != "All":
        where_clauses.append("language = %s")
        params.append(selected_language)

    if selected_statuses and len(selected_statuses) < len(statuses):
        placeholders = ','.join(['%s'] * len(selected_statuses))
        where_clauses.append(f"task_status IN ({placeholders})")
        params.extend(selected_statuses)

    if time_filter != "All Time" and start_date:
        where_clauses.append("DATE(updated_at) BETWEEN %s AND %s")
        params.extend([start_date, end_date])

    where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

    query_lang_status = f"""
    SELECT 
        language AS tgt_language,
        COUNT(CASE 
                 WHEN task_status IN ('annotated', 'reviewed', 'super_checked', 'exported') 
                 THEN 1 
             END) AS annotated_count,
        COUNT(CASE 
                 WHEN project_stage = '2' AND task_status IN ('reviewed', 'super_checked', 'exported') THEN 1
                 WHEN project_stage > '2' AND task_status IN ('reviewed', 'super_checked') THEN 1
             END) AS reviewed_count,
        COUNT(CASE 
                 WHEN project_stage = '3' AND task_status IN ('super_checked', 'exported') THEN 1
                 WHEN project_stage != '3' AND task_status = 'super_checked' THEN 1
             END) AS superchecked_count
    FROM intermediate_table
    {where_clause}
    GROUP BY language
    ORDER BY reviewed_count DESC;
    """

    df_lang_status = pd.read_sql(query_lang_status, conn, params=params)

    # Plotly Chart
    fig6 = go.Figure()
    fig6.add_trace(go.Bar(
        x=df_lang_status["tgt_language"],
        y=df_lang_status["annotated_count"],
        name="Annotated",
        marker_color="#3498DB"
    ))
    fig6.add_trace(go.Bar(
        x=df_lang_status["tgt_language"],
        y=df_lang_status["reviewed_count"],
        name="Reviewed",
        marker_color="#2ECC71"
    ))
    fig6.add_trace(go.Bar(
        x=df_lang_status["tgt_language"],
        y=df_lang_status["superchecked_count"],
        name="Superchecked",
        marker_color="#F39C12"
    ))

    # Dynamic Title
    title4 = " Task Status by Target Language"
    if selected_language != "All":
        title4 += f" - {selected_language}"
    if time_filter != "All Time":
        title4 += f" ({start_date} to {end_date})"

    fig6.update_layout(
        title=title4,
        barmode="stack",
        xaxis_title="Target Language",
        yaxis_title="Task Count",
        legend_title="Task Status",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)"
    )

    st.plotly_chart(fig6, use_container_width=True, key="chart4_fig")

    st.download_button(
        label="⬇️ Download Chart 4 Data as CSV",
        data=df_lang_status.to_csv(index=False),
        file_name="task_status_by_target_language_filtered.csv",
        mime="text/csv",
        key="chart4_download"
    )
