# #db.py
# #this code is used to connect to a PostgreSQL database using psycopg2 and Streamlit's caching mechanism.

import psycopg2
import streamlit as st

@st.cache_resource
def get_connection():
    try:
        conn = psycopg2.connect(
            host=st.secrets["database"]["host"],
            port=st.secrets["database"]["port"],
            dbname=st.secrets["database"]["dbname"],
            user=st.secrets["database"]["user"],
            password=st.secrets["database"]["password"]
        )
        return conn
    except Exception as e:
        st.error(f"❌ Database connection failed: {e}")
        return None

# import psycopg2
# import streamlit as st

# host = "e2e-97-65.ssdcloudindia.net"
# port = 5432
# dbname = "anudesh_monitoring"
# user = "admin"
# password = "9{L^O1hVIZsYBoDHIxjk${d9&k"

# @st.cache_resource
# def get_connection():
#     try:
#         conn = psycopg2.connect(
#             host=st.secrets["database"]["host"],
#             port=st.secrets["database"]["port"],
#             dbname=st.secrets["database"]["dbname"],
#             user=st.secrets["database"]["user"],
#             password=st.secrets["database"]["password"]
#         )
#         return conn
#     except Exception as e:
#         st.error(f"❌ Database connection failed: {e}")
#         return None
