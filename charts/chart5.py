# anudesh_dashboard/charts/chart5.py
import streamlit as st
import pandas as pd
import plotly.express as px
from itertools import product

# ------------------------
# Cached workspace loader
# ------------------------
# @st.cache_data
# def get_workspaces(conn):
#     with conn.cursor() as cur:
#         cur.execute("SELECT DISTINCT workspace_id FROM intermediate_table ORDER BY workspace_id;")
#         return [row[0] for row in cur.fetchall()]
@st.cache_data
def get_workspaces(_conn):
    with _conn.cursor() as cur:
        cur.execute("SELECT DISTINCT workspace_id FROM intermediate_table ORDER BY workspace_id;")
        return [row[0] for row in cur.fetchall()]

# -----------------------------------
# Get aggregated annotation stats
# -----------------------------------
def get_annotation_stats(conn, workspace_id):
    query = """
        SELECT 
            project_id,
            COUNT(*) AS total_tasks,
            COUNT(CASE 
                WHEN task_status IN ('annotated', 'reviewed', 'super_checked', 'exported') THEN 1
            END) AS annotated_count,
            COUNT(CASE 
                WHEN project_stage::INTEGER = 2 AND task_status IN ('reviewed', 'super_checked', 'exported') THEN 1
                WHEN project_stage::INTEGER > 2 AND task_status IN ('reviewed', 'super_checked') THEN 1
            END) AS reviewed_count
        FROM intermediate_table
        WHERE workspace_id = %s
        GROUP BY project_id
        ORDER BY project_id;
    """
    return pd.read_sql_query(query, conn, params=(workspace_id,))

# -----------------------------------
# Get drilldown annotation breakdown
# -----------------------------------
def get_annotation_details(conn, project_id):
    query= """SELECT
    project_id,
    annotation_status,
    CASE 
        WHEN annotation_status IN ('labeled', 'unlabeled') THEN 'annotated'
        WHEN annotation_status IN ('accepted_with_minor_changes', 'accepted_with_major_changes', 'unreviewed', 'accepted') THEN NULL
        WHEN task_status = 'annotated' THEN 'annotated'
        ELSE NULL
    END AS annotation_type,
    CASE 
        WHEN annotation_status IN ('accepted_with_minor_changes', 'accepted_with_major_changes', 'unreviewed', 'accepted') THEN 'reviewed'
        WHEN annotation_status IN ('labeled', 'unlabeled') THEN NULL
        WHEN task_status = 'reviewed' THEN 'reviewed'
        ELSE NULL
    END AS review_type
    FROM intermediate_table
    WHERE project_id = %s;
    """
    df = pd.read_sql_query(query, conn, params=(project_id,))

    records = []
    for _, row in df.iterrows():
        if row['annotation_type']:
            records.append(('annotated', row['annotation_status']))
        if row['review_type']:
            records.append(('reviewed', row['annotation_status']))

    df_clean = pd.DataFrame(records, columns=['Annotation Type', 'Annotation Status'])

    total_df = (
        df_clean.groupby('Annotation Type')
        .size()
        .reset_index(name='Count')
        .assign(**{'Annotation Status': 'total'})
    )

    combined_df = pd.concat([
        df_clean.value_counts().reset_index(name='Count'),
        total_df
    ], ignore_index=True)

    annotation_status_order = ['total'] + sorted(
        [s for s in combined_df['Annotation Status'].unique() if s != 'total']
    )
    combined_df['Annotation Status'] = pd.Categorical(
        combined_df['Annotation Status'],
        categories=annotation_status_order,
        ordered=True
    )

    return combined_df.sort_values(['Annotation Type', 'Annotation Status'])

# -----------------------------------
# Main Chart 5 Renderer
# -----------------------------------
def render_chart5(conn):
    st.markdown("---")
    st.markdown("### <a name='chart-5'></a>📈 Chart 5: Workspace level Annotation Stats", unsafe_allow_html=True)

    workspace_id = st.selectbox("Select a Workspace", get_workspaces(conn))

    if workspace_id:
        df = get_annotation_stats(conn, workspace_id)

        if df.empty:
            st.warning("No data found for this workspace.")
            return

        df_melted = df.melt(
            id_vars='project_id',
            value_vars=['total_tasks', 'annotated_count', 'reviewed_count'],
            var_name='Annotation Type',
            value_name='Count'
        )
        df_melted["project_id"] = df_melted["project_id"].astype(str)

        fig = px.bar(
            df_melted,
            x='project_id',
            y='Count',
            color='Annotation Type',
            barmode='group',
            title=f"Annotation Summary for Workspace {workspace_id}",
            text='Count'
        )
        fig.update_layout(
            xaxis_title="Project ID",
            yaxis_title="Count",
            xaxis=dict(type='category'),
            legend_title_text='Annotation Type'
        )
        fig.update_traces(
            textposition='inside',
            textangle=90,
            textfont_size=12,
            insidetextanchor='middle'
        )

        st.plotly_chart(fig, use_container_width=True)
        st.download_button(
            label="📥 Download Workspace Annotation Stats as CSV",
            data=df.to_csv(index=False).encode('utf-8'),
            file_name=f'workspace_{workspace_id}_annotation_stats.csv',
            mime='text/csv'
        )

        st.markdown("---")
        project_ids = df['project_id'].astype(str).tolist()
        selected_project = st.selectbox("Select a Project to Drill Down", project_ids)

        if selected_project:
            df_detail = get_annotation_details(conn, int(selected_project))

            if df_detail.empty:
                st.info("No annotation data for this project.")
                return

            annotation_types = ['annotated', 'reviewed']
            annotation_statuses = [
                'total',
                'labeled', 'unlabeled',
                'accepted', 'accepted_with_major_changes',
                'accepted_with_minor_changes', 'unreviewed'
            ]

            full_index = pd.DataFrame(
                list(product(annotation_types, annotation_statuses)),
                columns=['Annotation Type', 'Annotation Status']
            )

            df_detail = full_index.merge(df_detail, on=['Annotation Type', 'Annotation Status'], how='left').fillna(0)
            df_detail['Count'] = df_detail['Count'].astype(int)
            df_detail['Annotation Status'] = pd.Categorical(
                df_detail['Annotation Status'],
                categories=annotation_statuses,
                ordered=True
            )

            fig_detail = px.bar(
                df_detail[df_detail["Count"] > 0],
                x="Annotation Type",
                y="Count",
                color="Annotation Status",
                barmode="group",
                text="Count",
                title=f"Annotation Status Breakdown for Project {selected_project}"
            )
            fig_detail.update_layout(
                xaxis_title="Annotation Type",
                yaxis_title="Count",
                xaxis=dict(type='category'),
                legend_title_text='Annotation Status',
                bargap=0.15,
                bargroupgap=0
            )
            fig_detail.update_traces(
                textposition='inside',
                insidetextanchor='middle',
                textangle=0
            )

            st.plotly_chart(fig_detail, use_container_width=True, key=f"plotly_chart_{selected_project}")

            st.download_button(
                label="📥 Download Project Annotation Breakdown as CSV",
                data=df_detail.to_csv(index=False).encode('utf-8'),
                file_name=f'project_{selected_project}_annotation_breakdown.csv',
                mime='text/csv'
            )
        else:
            st.info("Please select a project to view detailed annotation breakdown.")