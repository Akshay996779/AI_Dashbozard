import streamlit as st
import pandas as pd
import datetime
from PIL import Image
import plotly.express as px
import plotly.graph_objects as go
import os
import google.generativeai as genai

# Configure Gemini
genai.configure(api_key="AIzaSyDcgtW4LS1Qyn2eO8FMI13cCGLeJOhOYn4")
model = genai.GenerativeModel("models/gemini-1.5-flash")

# Load Excel file
file_path = "Adidas.xlsx"
try:
    df = pd.read_excel(file_path)
except FileNotFoundError:
    st.error(f"Error: File not found at {file_path}")
    st.stop()

# Prepare Month-Year column
df["Month_Year"] = df["InvoiceDate"].dt.strftime("%b'%y")

# -------------- Streamlit UI -----------------
st.set_page_config(page_title="Sales Dashboard", layout="wide")
st.title("Sales Dashboard + AI Assistant")

# Logo and Title
col1, col2 = st.columns([0.1, 0.9])
with col1:
    image = Image.open("adidas-logo.jpg")
    st.image(image, width=80)
with col2:
    st.markdown("""
        <style>
        .title-test { font-weight:bold; padding:5px; border-radius:6px; }
        </style>
        <h1 class="title-test">Interactive Sales Dashboard</h1>
    """, unsafe_allow_html=True)
    st.write(f"Last updated: {datetime.datetime.now().strftime('%d %B %Y')}")

# -------------- Sidebar Filters -----------------
st.sidebar.header("🔎 Apply Filters")

region_filter = st.sidebar.selectbox("Select Region", ["All"] + sorted(df["Region"].dropna().unique()))
retailer_filter = st.sidebar.selectbox("Select Retailer", ["All"] + sorted(df["Retailer"].dropna().unique()))
state_filter = st.sidebar.selectbox("Select State", ["All"] + sorted(df["State"].dropna().unique()))
month_filter = st.sidebar.selectbox("Select Month-Year", ["All"] + sorted(df["Month_Year"].dropna().unique()))

filtered_df = df.copy()
if region_filter != "All":
    filtered_df = filtered_df[filtered_df["Region"] == region_filter]
if retailer_filter != "All":
    filtered_df = filtered_df[filtered_df["Retailer"] == retailer_filter]
if state_filter != "All":
    filtered_df = filtered_df[filtered_df["State"] == state_filter]
if month_filter != "All":
    filtered_df = filtered_df[filtered_df["Month_Year"] == month_filter]

# -------------- Gemini Chat -----------------
st.sidebar.header("💬 Chat with Highbar Bot")
user_input = st.sidebar.text_area("Ask a question about filtered data:")

if st.sidebar.button("Enter") and user_input:
    prompt = f"""
You are an intelligent data analyst working with this filtered dataset:
Columns: {', '.join(filtered_df.columns)}

Here is a sample of the data:
{filtered_df.head(5).to_csv(index=False)}

The user asks:
"{user_input}"

Please provide a clear, concise response based only on the above data.
"""
    try:
        response = model.generate_content(prompt)
        st.sidebar.success("Response:")
        st.sidebar.write(response.text)
    except Exception as e:
        st.sidebar.error(f"Gemini Error: {e}")

# -------------- Natural Language → Chart -------------
st.sidebar.header("📊 Ask for a Chart")
chart_request = st.sidebar.text_area("Describe the chart (e.g., bar chart of TotalSales by Region):")

if st.sidebar.button("Generate Chart") and chart_request:
    chart_prompt = f"""
You are a Python data visualization assistant.

Based on this pandas DataFrame with the following columns:
{', '.join(filtered_df.columns)}

Write valid Python code using Plotly Express (px) to plot a {chart_request}.
Use 'filtered_df' as the DataFrame.
Do not include import statements or display commands.
Just return the code starting with: fig = px...

Example output:
fig = px.bar(filtered_df, x='Region', y='TotalSales')
"""
    try:
        chart_response = model.generate_content(chart_prompt)
        chart_code = chart_response.text.strip()

        if "fig = px." in chart_code:
            st.sidebar.success("Chart generated successfully!")
            st.code(chart_code, language="python")
            try:
                exec(chart_code, globals())  # Executes code to create `fig`
                st.plotly_chart(fig, use_container_width=True)
            except Exception as plot_err:
                st.error(f"Error rendering chart: {plot_err}")
        else:
            st.sidebar.error("Gemini could not generate a chart.")
    except Exception as e:
        st.sidebar.error(f"Gemini Chart Error: {e}")

# -------------- Dashboard Charts -----------------

# Chart 1: Total Sales by Retailer
st.markdown("### 📊 Total Sales by Retailer")
fig1 = px.bar(filtered_df, x="Retailer", y="TotalSales", labels={"TotalSales": "Total Sales ($)"},
              template="gridon", hover_data=["TotalSales"])
st.plotly_chart(fig1, use_container_width=True)

with st.expander("View Retailer-wise Data"):
    grouped = filtered_df.groupby("Retailer")["TotalSales"].sum().reset_index()
    st.dataframe(grouped)
st.download_button("Download Retailer Data", data=grouped.to_csv().encode("utf-8"), file_name="RetailerSales.csv")

# Chart 2: Monthly Sales
st.markdown("### 📈 Monthly Sales Trend")
monthly_sales = filtered_df.groupby("Month_Year")["TotalSales"].sum().reset_index()
fig2 = px.line(monthly_sales, x="Month_Year", y="TotalSales", template="gridon")
st.plotly_chart(fig2, use_container_width=True)

with st.expander("View Monthly Sales Data"):
    st.dataframe(monthly_sales)
st.download_button("Download Monthly Sales", data=monthly_sales.to_csv().encode("utf-8"), file_name="MonthlySales.csv")

# Chart 3: Sales and Units by State
st.markdown("### 🌎 Total Sales and Units Sold by State")
statewise = filtered_df.groupby("State")[["TotalSales", "UnitsSold"]].sum().reset_index()
fig3 = go.Figure()
fig3.add_trace(go.Bar(x=statewise["State"], y=statewise["TotalSales"], name="Total Sales"))
fig3.add_trace(go.Scatter(x=statewise["State"], y=statewise["UnitsSold"], mode="lines+markers",
                          name="Units Sold", yaxis="y2"))
fig3.update_layout(
    yaxis=dict(title="Total Sales"),
    yaxis2=dict(title="Units Sold", overlaying="y", side="right"),
    template="gridon"
)
st.plotly_chart(fig3, use_container_width=True)

with st.expander("View Sales & Units Data"):
    st.dataframe(statewise)
st.download_button("Download State Data", data=statewise.to_csv().encode("utf-8"), file_name="StatewiseSales.csv")

# Chart 4: Treemap
st.markdown("### 🗺️ Sales by Region and City")
treemap = filtered_df.groupby(["Region", "City"])["TotalSales"].sum().reset_index()
treemap["TotalSales (Formatted)"] = treemap["TotalSales"].apply(lambda x: f"{x/1_00_000:.2f} Lakh")
fig4 = px.treemap(treemap, path=["Region", "City"], values="TotalSales",
                  hover_name="TotalSales (Formatted)", color="City")
st.plotly_chart(fig4, use_container_width=True)

with st.expander("View Region-City Sales Data"):
    st.dataframe(treemap)
st.download_button("Download Region Data", data=treemap.to_csv().encode("utf-8"), file_name="RegionCitySales.csv")

# Raw Data View
with st.expander("📄 View Filtered Dataset"):
    st.dataframe(filtered_df)
st.download_button("Download Raw Data", data=filtered_df.to_csv().encode("utf-8"), file_name="FilteredSalesData.csv")

