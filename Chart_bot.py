import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai

# Configure Gemini
genai.configure(api_key="AIzaSyDcgtW4LS1Qyn2eO8FMI13cCGLeJOhOYn4")
model = genai.GenerativeModel("models/gemini-1.5-flash")

# Load Excel file
file_path = "C:/Users/Akshay Rokade/Downloads/Python dashboard/Adidas.xlsx"
try:
    df = pd.read_excel(file_path)
except FileNotFoundError:
    st.error(f"Error: File not found at {file_path}")
    st.stop()

# Prepare Month-Year column
df["Month_Year"] = df["InvoiceDate"].dt.strftime("%b'%y")

# Streamlit Page
st.set_page_config(page_title="AI Chart Generator", layout="wide")
st.title("AI Chart Generator (Gemini)")

# -------- Gemini Chart Only ----------
st.sidebar.header("📊 Ask for a Chart")
chart_request = st.sidebar.text_area("Describe the chart (e.g., bar chart of TotalSales by Region):")

if st.sidebar.button("Generate Chart") and chart_request:
    chart_prompt = f"""
You are a Python data visualization assistant.

Based on this pandas DataFrame with the following columns:
{', '.join(df.columns)}

Write valid Python code using Plotly Express (px) to plot a {chart_request}.
Use 'df' as the DataFrame.
Do not include import statements or display commands.
Just return the code starting with: fig = px...

Example output:
fig = px.bar(df, x='Region', y='TotalSales')
"""
    try:
        chart_response = model.generate_content(chart_prompt)
        chart_code = chart_response.text.strip()

        if "fig = px." in chart_code:
            st.sidebar.success("Chart generated successfully!")
            st.code(chart_code, language="python")
            try:
                exec(chart_code, globals())  # Executes code to create 'fig'
                st.plotly_chart(fig, use_container_width=True)
            except Exception as plot_err:
                st.error(f"❌ Error rendering chart: {plot_err}")
        else:
            st.sidebar.error("❌ Gemini could not generate a valid chart.")
    except Exception as e:
        st.sidebar.error(f"Gemini Chart Error: {e}")

# ------------------ ALL BELOW COMMENTED OUT --------------------
# st.sidebar.header("🔎 Apply Filters")
# region_filter = st.sidebar.selectbox("Select Region", ["All"] + sorted(df["Region"].dropna().unique()))
# ...
# st.markdown("### 📊 Total Sales by Retailer")
# fig1 = px.bar(filtered_df, x="Retailer", y="TotalSales", ...)
# st.plotly_chart(fig1, use_container_width=True)
# ...
# with st.expander("📄 View Filtered Dataset"):
#     st.dataframe(filtered_df)
# st.download_button("Download Raw Data", ...)

