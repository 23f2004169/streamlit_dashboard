

# anudesh_dashboard/charts/chart2.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import datetime
from utils import apply_time_filter
from .excel_export import generate_language_excel

def render_chart2(conn, color_map):
    st.markdown("---")
    st.markdown("### <a name='chart-2'></a>📈 Chart 2: Planned vs Actual Annotations (by Language & Script Type)", unsafe_allow_html=True)

    query_lang = """
    SELECT 
        category,
        language,
        script_type,
        SUM(planned) AS planned,
        SUM(actual) AS actual,
        MIN(updated_at) AS updated_at 
    FROM language_table
    WHERE language IS NOT NULL AND language <> '' AND LOWER(language) NOT IN ('filipino', 'english')
    GROUP BY category, language, script_type 
    ORDER BY language, script_type;
    """
    df_lang = pd.read_sql(query_lang, conn)

    if df_lang["updated_at"].dtype == "object" or isinstance(df_lang["updated_at"].iloc[0], datetime.time):
        df_lang["updated_at"] = df_lang["updated_at"].apply(
            lambda t: datetime.datetime.combine(datetime.date.today(), t)
            if isinstance(t, datetime.time)
            else pd.to_datetime(t, errors='coerce')
        )
    else:
        df_lang["updated_at"] = pd.to_datetime(df_lang["updated_at"], errors='coerce')

    col5, col6 = st.columns([2, 1])
    with col5:
        time_filter2 = st.radio(
            "⏱ Time Range",
            ["All Time", "Today", "Yesterday", "Last Week", "Last Month", "Custom Range"],
            key="time2",
            horizontal=True
        )
    with col6:
        categories2 = ["All"] + sorted(df_lang["category"].dropna().unique())
        selected_category2 = st.selectbox("Select Category", options=categories2, key="cat2")

        col_script, col_lang = st.columns(2)
        with col_script:
            script_types2 = ["All"] + sorted(df_lang["script_type"].dropna().unique())
            selected_script_type2 = st.selectbox("Select Script Type", options=script_types2, key="stype2")

        with col_lang:
            languages2 = ["All"] + sorted(df_lang["language"].dropna().unique())
            selected_language2 = st.selectbox("Select Language", options=languages2, key="lang2")

    df2_filtered = apply_time_filter(df_lang.copy(), time_filter2)

    if selected_category2 != "All":
        df2_filtered = df2_filtered[df2_filtered["category"] == selected_category2]

    if selected_script_type2 != "All":
        df2_filtered = df2_filtered[df2_filtered["script_type"] == selected_script_type2]

    if selected_language2 != "All":
        df2_filtered = df2_filtered[df2_filtered["language"] == selected_language2]

    df2_filtered.dropna(subset=["language", "script_type", "planned", "actual"], inplace=True)
    df2_filtered["planned"] = pd.to_numeric(df2_filtered["planned"], errors="coerce")
    df2_filtered["actual"] = pd.to_numeric(df2_filtered["actual"], errors="coerce")
    df2_filtered["language"] = df2_filtered["language"].apply(lambda x: ', '.join(x) if isinstance(x, list) else str(x))

    fig3 = go.Figure()
    script_types = sorted([s for s in df2_filtered["script_type"].dropna().unique()])
    languages = df2_filtered["language"].unique()

    for stype in script_types:
        for typ in ["planned", "actual"]:
            subset = df2_filtered[df2_filtered["script_type"] == stype]
            y_vals, langs = [], []
            for lang in languages:
                value = subset[subset["language"] == lang][typ].sum()
                if value > 0:
                    y_vals.append(value)
                    langs.append(lang)
            fig3.add_trace(go.Bar(
                x=langs,
                y=y_vals,
                name=f"{typ.capitalize()} - {stype}",
                marker_color=color_map.get((stype, typ), "#cccccc"),
                offsetgroup=typ,
                legendgroup=stype,
                text=y_vals,
                textposition="auto"
            ))

    fig3.update_layout(
        xaxis_title="Language",
        yaxis_title="Annotation Count",
        barmode="stack",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        legend_title="Script Type + Type"
    )
    st.plotly_chart(fig3, use_container_width=True)

    # Excel download button
    output = generate_language_excel(df2_filtered)
    st.download_button(
        label="📥 Download High level Language Report ",
        data=output,
        file_name="language_report_filled.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # Language Drilldown
    available_langs = ["--Select a Language--"] + sorted(df2_filtered["language"].unique())
    selected_language = st.selectbox("Select a Language to Drill Down", options=available_langs)

    if selected_language != "--Select a Language--":
        lang_df = df2_filtered[df2_filtered["language"] == selected_language].copy()
        lang_df = lang_df.groupby("script_type")[["planned", "actual"]].sum().reset_index()
        lang_df.sort_values("planned", ascending=False, inplace=True)

        lang_fig = go.Figure()
        lang_fig.add_trace(go.Bar(
            x=lang_df["script_type"],
            y=lang_df["planned"],
            name="Planned",
            marker_color="#5DADE2",
            text=lang_df["planned"],
            textposition="auto"
        ))
        lang_fig.add_trace(go.Bar(
            x=lang_df["script_type"],
            y=lang_df["actual"],
            name="Actual",
            marker_color="#48C9B0",
            text=lang_df["actual"],
            textposition="auto"
        ))
        lang_fig.update_layout(
            title=f"📌 Detailed Breakdown for Language: '{selected_language}'",
            xaxis_title="Script Type",
            yaxis_title="Annotation Count",
            barmode="group",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            legend_title="Annotation Type"
        )
        st.plotly_chart(lang_fig, use_container_width=True)

    return df2_filtered
