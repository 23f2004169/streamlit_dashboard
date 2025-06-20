import streamlit as st
from db import get_connection
from charts.chart1 import render_chart1
from charts.chart2 import render_chart2
from charts.chart3 import render_chart3
from charts.chart4 import render_chart4
from charts.chart5 import render_chart5 

st.set_page_config(page_title="Anudesh Annotation Dashboard", layout="wide")
st.title("Anudesh Annotation Dashboard")
st.markdown("---")

st.markdown("""
### 📊 Report Index  
🔹 [Chart 1: Planned vs Actual Annotations (by Category & Script Type)](#chart-1)  
🔹 [Chart 2: Planned vs Actual Annotations (by Language & Script Type)](#chart-2)  
🔹 [Chart 3: Daily User Progress ](#chart-3)  
🔹 [Chart 4: Task Status by Target Language](#chart-4)  
🔹 [Chart 5: Workspace level Annotation Stats](#chart-5)
""", unsafe_allow_html=True)

conn = get_connection()
if conn:
    st.markdown("---")
    
    # ----- Chart 1: Category & Script Type -----
    render_chart1(conn)

    color_map = {
    # Blue shades for English
    ("English", "planned"): "#B3D4FC",   # Light Blue
    ("English", "actual"): "#1F77B4",    # Medium/Darker Blue

    # Green shades for Native
    ("Native", "planned"): "#BDEDB3",    # Light Green
    ("Native", "actual"): "#2CA02C",     # Medium/Darker Green

    # Yellow shades for Indic Roman
    ("Indic Roman", "planned"): "#FFF4B3",  # Light Yellow
    ("Indic Roman", "actual"): "#FFBB00",   # Medium/Darker Yellow
}


    # ----- Chart 2: Language & Script Type -----
    render_chart2(conn, color_map)

    # ----- Chart 3: Daily User Progress -----
    render_chart3(conn)

    # ----- Chart 4: Task Status by Target Language -----
    render_chart4(conn)

    # ----- Chart 5: Workspace level Annotation Stats -----
    render_chart5(conn)

    st.markdown("---")
else:
    st.error("Failed to connect to the database. Please check your connection settings.")


