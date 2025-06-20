import datetime as dt
import streamlit as st

def apply_time_filter(df, time_filter):
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
            start_date = st.date_input("Start Date", value=today - dt.timedelta(days=30), key="s1")
        with col4:
            end_date = st.date_input("End Date", value=today, key="e1")

    if time_filter != "All Time" and start_date:
        df = df[(df["updated_at"].dt.date >= start_date) & (df["updated_at"].dt.date <= end_date)]
    return df
