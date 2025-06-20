#db.py
#this code is used to connect to a PostgreSQL database using psycopg2 and Streamlit's caching mechanism.
import psycopg2
import streamlit as st

DB_HOST = 'localhost'
DB_PORT = "5432"
DB_NAME = 'Summary_Report'
DB_USER = 'postgres'
DB_PASS = 'postgres'

# Database connection function for Streamlit app
@st.cache_resource
def get_connection():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
        # st.success("✅ Successfully connected to the database.")
        return conn
    except Exception as e:
        # st.error(f"❌ Database connection failed: {e}")
        return None
