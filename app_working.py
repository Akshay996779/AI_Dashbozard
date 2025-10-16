import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
import google.generativeai as genai
import os

# ------------------------------
# 1️⃣ Configure Google Gemini API
# ------------------------------
os.environ["GOOGLE_API_KEY"] = "AIzaSyA4E4VJnUbG3lONWs1hdg2JTUbaAKkGuX0"  # Replace with your key
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

# ------------------------------
# 2️⃣ Streamlit Page Setup
# ------------------------------
st.set_page_config(page_title="MySQL Gemini Chatbot", layout="wide")
st.title("🤖 SQL Chatbot using Google Gemini + MySQL")

# ------------------------------
# 3️⃣ Sidebar: MySQL Credentials
# ------------------------------
st.sidebar.header("MySQL Connection Settings")
host = st.sidebar.text_input("Host", value="127.0.0.1")
port = st.sidebar.text_input("Port", value="3306")
user = st.sidebar.text_input("User", value="root")
password = st.sidebar.text_input("Password", type="password")
database = st.sidebar.text_input("Database", value="Chinook")

# ------------------------------
# 4️⃣ Connect to MySQL safely
# ------------------------------
def connect_to_mysql(host, port, user, password, database):
    try:
        safe_password = quote_plus(password)  # Encode special characters
        db_uri = f"mysql+mysqlconnector://{user}:{safe_password}@{host}:{port}/{database}"
        engine = create_engine(db_uri)
        conn = engine.connect()
        return conn
    except Exception as e:
        st.sidebar.error(f"❌ Connection failed: {str(e)}")
        return None

if "conn" not in st.session_state:
    st.session_state.conn = None

if st.sidebar.button("Connect"):
    st.sidebar.info("Connecting...")
    st.session_state.conn = connect_to_mysql(host, port, user, password, database)
    if st.session_state.conn:
        st.sidebar.success(f"✅ Connected to MySQL database '{database}'")

# ------------------------------
# 5️⃣ Get Schema Info
# ------------------------------
def get_schema(conn):
    try:
        query = "SHOW TABLES;"
        result = conn.execute(text(query))
        tables = [row[0] for row in result.fetchall()]
        schema_info = ""
        for table in tables:
            columns_result = conn.execute(text(f"SHOW COLUMNS FROM {table}"))
            columns = [f"{col[0]} ({col[1]})" for col in columns_result.fetchall()]
            schema_info += f"Table {table}: {', '.join(columns)}\n"
        return schema_info
    except Exception as e:
        st.error(f"❌ Error fetching schema: {e}")
        return ""

if st.session_state.conn:
    st.session_state.schema_info = get_schema(st.session_state.conn)

# ------------------------------
# 6️⃣ Gemini Query Function (Improved)
# ------------------------------
def ask_gemini(user_input, schema_info, chat_history):
    try:
        model = genai.GenerativeModel("models/gemini-2.5-flash")

        prompt = f"""
        You are a MySQL expert. Based on the following schema, write a valid MySQL query.
        Return ONLY the SQL query — do not include 'sql' prefix, markdown, or explanation.

        Schema:
        {schema_info}

        Question:
        {user_input}
        """

        response = model.generate_content(prompt)

        if hasattr(response, "text"):
            sql_query = response.text.strip()

            # 🧹 Clean up: remove unwanted prefixes and code fences
            sql_query = (
                sql_query.replace("```sql", "")
                .replace("```", "")
                .replace("SQL", "")
                .replace("sql", "")
                .strip()
            )

            return sql_query
        else:
            st.warning("⚠️ Gemini did not return a SQL query.")
            return ""
    except Exception as e:
        st.error(f"❌ Gemini API Error: {e}")
        return ""

# ------------------------------
# 7️⃣ Run SQL Query (Improved)
# ------------------------------
def run_query(conn, query):
    try:
        clean_query = query.strip().strip(";")
        result = conn.execute(text(clean_query))
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
        return df
    except Exception as e:
        st.error(f"❌ SQL Execution Error: {e}")
        st.code(query, language="sql")
        return None

# ------------------------------
# 8️⃣ Chat Interface
# ------------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

user_input = st.text_input("Ask a question about your database:")

if user_input and st.session_state.conn:
    st.session_state.chat_history.append(f"Human: {user_input}")

    sql_query = ask_gemini(user_input, st.session_state.schema_info, st.session_state.chat_history)
    
    if sql_query:
        df_result = run_query(st.session_state.conn, sql_query)
        if df_result is not None:
            st.dataframe(df_result)
    else:
        st.warning("⚠️ No SQL query generated by Gemini.")

    st.session_state.chat_history.append(f"AI: {sql_query}")
