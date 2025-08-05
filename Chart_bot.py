import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import datetime
import google.generativeai as genai
import io
import contextlib
import os

# Configure Gemini
genai.configure(api_key="AIzaSyDcgtW4LS1Qyn2eO8FMI13cCGLeJOhOYn4")
model = genai.GenerativeModel("models/gemini-1.5-flash")

# Streamlit UI setup
st.set_page_config(page_title="ChartBot", layout="wide")
st.title("📊 ChartBot - Ask for Any Chart")

# Load Excel file from a consistent working local path (same as App 1)
file_path = "C:/Users/Akshay Rokade/Downloads/Chartbot/Adidas.xlsx"
try:
    if not os.path.exists(file_path):
        raise FileNotFoundError
    df = pd.read_excel(file_path)
except FileNotFoundError:
    st.error(f"❌ Local file not found at: {file_path}")
    st.stop()
except Exception as e:
    st.error(f"❌ Error reading Excel file: {e}")
    st.stop()

# Prepare Month-Year column
if "InvoiceDate" in df.columns:
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")
    df["Month_Year"] = df["InvoiceDate"].dt.strftime("%b'%y")

# Display last updated time
st.write(f"Last updated: {datetime.datetime.now().strftime('%d %B %Y')}")

# Text input for chart request
st.header("🧠 Ask for a Chart")
chart_request = st.text_area("Describe the chart you want (e.g., bar chart of TotalSales by Region):")

if st.button("Generate Chart") and chart_request:
    chart_prompt = f"""
You are a Python data visualization assistant.

Using this pandas DataFrame with columns:
{', '.join(df.columns)}

Generate valid and visually appealing Python code using Plotly (express or graph_objects) to visualize this request:
\"{chart_request}\"

Use 'df' as the DataFrame.
Use a qualitative color palette like 'Plotly' or 'D3' to assign different colors to categorical variables.
Ensure the chart is highly attractive, clear, and uses professional formatting with labels, titles, hover tooltips, layout tweaks, legends.
Remove all background grid lines from the chart.
Avoid calling fig.show().
Use best practices to improve readability and aesthetics.
If appropriate, create subplots, dual axes, or advanced chart types.
"""
    try:
        chart_response = model.generate_content(chart_prompt)
        chart_code = chart_response.text.strip()

        # Extract only the code block if wrapped with triple backticks
        if "```" in chart_code:
            chart_code = chart_code.split("```python")[-1].split("```")[-2].strip()

        if "fig =" in chart_code:
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    exec(chart_code, globals())
                st.plotly_chart(fig, use_container_width=True)
            except Exception as plot_err:
                st.error(f"❌ Error rendering chart: {plot_err}")
        else:
            st.error("❌ Gemini could not generate a chart. Try a more specific request.")
    except Exception as e:
        st.error(f"❌ Gemini Chart Error: {e}")
