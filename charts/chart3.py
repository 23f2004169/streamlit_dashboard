import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import datetime as dt
from utils import apply_time_filter

def render_chart3(conn):
    st.markdown("---")
    st.markdown("### <a name='chart-3'></a>📈 Chart 3: Daily User Progress (Filtered)", unsafe_allow_html=True)

    base_query = """
        SELECT DISTINCT language, user_first_name, user_last_name, category, 
               CAST(workspace_id AS TEXT) AS workspace_id 
        FROM intermediate_table 
        WHERE language IS NOT NULL 
              AND user_first_name IS NOT NULL 
              AND user_last_name IS NOT NULL
              AND category IS NOT NULL 
              AND workspace_id IS NOT NULL
    """
    df_filters = pd.read_sql(base_query, conn)
    df_filters["user_full_name"] = df_filters["user_first_name"] + " " + df_filters["user_last_name"]

    st.markdown("####  Apply Filters")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        selected_language = st.selectbox(
            "🎙️ Select Language", 
            ["All"] + sorted(df_filters["language"].unique().tolist()), 
            index=0, key="c3_language"
        )

    df_filtered = df_filters.copy()
    if selected_language != "All":
        df_filtered = df_filtered[df_filtered["language"] == selected_language]

    with col2:
        users = sorted(df_filtered["user_full_name"].unique().tolist())
        selected_user = st.selectbox(
            "👤 Select User", ["All"] + users, index=0, key="c3_user"
        )

    if selected_user != "All":
        df_filtered = df_filtered[df_filtered["user_full_name"] == selected_user]
        selected_first_name = df_filtered["user_first_name"].iloc[0]
        selected_last_name = df_filtered["user_last_name"].iloc[0]

    with col3:
        categories = sorted(df_filtered["category"].unique().tolist())
        selected_category = st.selectbox(
            "🏷️ Select Category", ["All"] + categories, index=0, key="c3_category"
        )

    if selected_category != "All":
        df_filtered = df_filtered[df_filtered["category"] == selected_category]

    with col4:
        workspaces = sorted(df_filtered["workspace_id"].unique().tolist())
        selected_workspace = st.selectbox(
            "📂 Select Workspace ID", ["All"] + workspaces, index=0, key="c3_workspace"
        )

    time_filter = st.radio(
        "⏱ Time Range", 
        ["All Time", "Today", "Yesterday", "Last Week", "Last Month", "Custom Range"], 
        horizontal=True, key="c3_time"
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
        col5, col6 = st.columns(2)
        with col5:
            start_date = st.date_input("Start Date", value=today - dt.timedelta(days=30), key="c3_start")
        with col6:
            end_date = st.date_input("End Date", value=today, key="c3_end")

    where_clauses = []
    params = []

    if selected_language != "All":
        where_clauses.append("language = %s")
        params.append(selected_language)

    if selected_user != "All":
        where_clauses.append("user_first_name = %s AND user_last_name = %s")
        params.extend([selected_first_name, selected_last_name])

    if selected_category != "All":
        where_clauses.append("category = %s")
        params.append(selected_category)

    if selected_workspace != "All":
        where_clauses.append("CAST(workspace_id AS TEXT) = %s")
        params.append(selected_workspace)

    if time_filter != "All Time" and start_date:
        where_clauses.append("DATE(updated_at) BETWEEN %s AND %s")
        params.extend([start_date, end_date])

    where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

    day_type = st.radio(
        "🗕 Day Type", 
        ["All Days", "Weekdays Only", "Weekends Only"], 
        horizontal=True, key="c3_daytype"
    )

    query_progress = f"""
    SELECT 
        DATE(updated_at) AS work_date, 
        user_first_name,
        user_last_name,
        category,
        COUNT(*) AS annotations_done
    FROM intermediate_table
    {where_clause}
    GROUP BY work_date, user_first_name, user_last_name, category
    ORDER BY work_date ASC;
    """

    df_progress = pd.read_sql(query_progress, conn, params=params)
    df_progress["work_date"] = pd.to_datetime(df_progress["work_date"])

    if day_type == "Weekdays Only":
        df_progress = df_progress[df_progress["work_date"].dt.weekday < 5]
    elif day_type == "Weekends Only":
        df_progress = df_progress[df_progress["work_date"].dt.weekday >= 5]

    df_progress["user_full_name"] = df_progress["user_first_name"] + " " + df_progress["user_last_name"]

    fig4 = go.Figure()
    fig4.add_trace(go.Scatter(
        x=df_progress["work_date"],
        y=df_progress["annotations_done"],
        mode="lines+markers",
        name="Annotations Done",
        marker=dict(color="#F39C12"),
        line=dict(width=2)
    ))

    title_text = " Daily User Progress"
    if selected_user != "All":
        title_text += f" for {selected_user}"
    if selected_category != "All":
        title_text += f" in '{selected_category}'"
    if selected_workspace != "All":
        title_text += f" (Workspace ID: {selected_workspace})"
    if selected_language != "All":
        title_text += f" in language '{selected_language}'"
    if time_filter != "All Time":
        title_text += f" ({start_date} to {end_date})"

    fig4.update_layout(
        title=title_text,
        xaxis_title="Date",
        yaxis_title="Annotations Done",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)"
    )

    st.plotly_chart(fig4, use_container_width=True, key="chart3_fig")

    st.download_button(
        label="⬇️ Download Chart 3 Data as CSV",
        data=df_progress.to_csv(index=False),
        file_name="daily_user_progress_filtered.csv",
        mime="text/csv",
        key="chart3_download"
    )
