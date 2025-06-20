# anudesh_dashboard/charts/chart1.py
import pandas as pd 
import plotly.graph_objects as go
import streamlit as st
from utils import apply_time_filter


def render_chart1(conn):
    st.markdown("### <a name='chart-1'></a>📈 Chart 1: Planned vs Actual Annotations (by Category & Script Type)", unsafe_allow_html=True)
    query_script_type= """
        SELECT 
            category,
            script_type,
            SUM(planned) AS planned,
            SUM(actual) AS actual,
            MIN(updated_at) AS updated_at
        FROM language_table
        GROUP BY category, script_type
        ORDER BY category, script_type;
        """     
    df = pd.read_sql(query_script_type, conn)
    df["updated_at"] = pd.to_datetime(df["updated_at"], errors='coerce')

    planned_ref = df[["category", "script_type", "planned"]].copy()
    all_categories = df["category"].unique()
    all_scripts = df["script_type"].unique()
    full_index = pd.MultiIndex.from_product([all_categories, all_scripts], names=["category", "script_type"])
    planned_ref = planned_ref.set_index(["category", "script_type"]).reindex(full_index, fill_value=0).reset_index()

    col1, col2 = st.columns([2, 1])
    with col1:
        time_filter1 = st.radio(
            "⏱ Time Range",
            ["All Time", "Today", "Yesterday", "Last Week", "Last Month", "Custom Range"],
            key="time1",
            horizontal=True
        )
    with col2:
        categories1 = sorted(df["category"].unique())
        selected_categories1 = st.multiselect(" Select Categories", options=categories1, default=categories1, key="cat1")

    filtered_df = apply_time_filter(df.copy(), time_filter1)
    filtered_df = filtered_df[filtered_df["category"].isin(selected_categories1)]

    merged_df = filtered_df.drop(columns=["planned"]).merge(planned_ref, on=["category", "script_type"], how="right")
    merged_df = merged_df[merged_df["category"].isin(selected_categories1)].fillna({"actual": 0})

    script_types = sorted([s for s in merged_df["script_type"].dropna().unique()])
    categories = sorted(selected_categories1)
    color_map = {
        ("English", "planned"): "#B3D4FC", ("English", "actual"): "#1F77B4",
        ("Native", "planned"): "#BDEDB3", ("Native", "actual"): "#2CA02C",
        ("Indic Roman", "planned"): "#FFF4B3", ("Indic Roman", "actual"): "#FFBB00",
    }

    fig = go.Figure()
    for script in script_types:
        for typ in ["planned", "actual"]:
            data = merged_df[merged_df["script_type"] == script]
            y_vals = [data[(data["category"] == cat)][typ].values[0] if not data[(data["category"] == cat)][typ].empty else 0 for cat in categories]
            fig.add_trace(go.Bar(
                x=categories,
                y=y_vals,
                name=f"{script} ({typ.capitalize()})",
                marker_color=color_map.get((script, typ), "#cccccc"),
                offsetgroup=typ,
                legendgroup=script,
                text=["0" if v == 0 else f"{v:.0f}" for v in y_vals],
                textposition="outside",
                texttemplate="%{text}",
                cliponaxis=False
            ))

    fig.update_layout(
        xaxis_title="Category",
        yaxis_title="Annotation Count",
        barmode="stack",
        legend_title="Script Type & Annotation Type",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        bargap=0.25
    )

    st.plotly_chart(fig, use_container_width=True)

    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="⬇️ Download Chart 1 data as CSV",
        data=csv,
        file_name="filtered_annotations_chart1.csv",
        mime="text/csv"
    )

    render_chart1_drilldown(filtered_df, selected_categories1)


def render_chart1_drilldown(df1_filtered, categories):
    st.markdown("### 📌 Category Drilldown")

    category_options = ["-- Select a category --"] + sorted(categories)
    selected_category = st.selectbox("Select a Category to Drill Down", options=category_options)

    if selected_category != "-- Select a category --":
        detail_df = df1_filtered[df1_filtered["category"] == selected_category]
        detail_fig = go.Figure()
        detail_fig.add_trace(go.Bar(
            x=detail_df["script_type"],
            y=detail_df["planned"],
            name="Planned",
            marker_color="#5DADE2",
            text=detail_df["planned"],
            textposition="auto"
        ))
        detail_fig.add_trace(go.Bar(
            x=detail_df["script_type"],
            y=detail_df["actual"],
            name="Actual",
            marker_color="#48C9B0",
            text=detail_df["actual"],
            textposition="auto"
        ))
        detail_fig.update_layout(
            title=f"Detailed Breakdown for '{selected_category}'",
            xaxis_title="Script Type",
            yaxis_title="Annotation Count",
            barmode="group",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(detail_fig, use_container_width=True)
