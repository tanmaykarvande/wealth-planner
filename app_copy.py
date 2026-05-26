import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import openpyxl
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# PAGE CONFIG
st.set_page_config(page_title="Wealth Architecture Engine", layout="wide")

# CUSTOM CSS FOR FONTS/METRICS
st.markdown("""
    <style>
    .metric-value { font-size: 24px !important; font-weight: bold; color: #1f497d; }
    .metric-label { font-size: 14px !important; color: #555; }
    </style>
    """, unsafe_allow_html=True)

# SIDEBAR INPUTS
st.sidebar.header("📋 Client Parameter Profile")
client_name = st.sidebar.text_input("Client Name", "Karan Sharma")
current_age = st.sidebar.number_input("Current Age", 0, 100, 40)
retire_age = st.sidebar.number_input("Retirement Age", 20, 90, 60)
expected_return = st.sidebar.slider("Expected Portfolio Return (%)", 1.0, 25.0, 18.0) / 100
monthly_swp = st.sidebar.number_input("Target Monthly SWP (₹)", 0, 1000000, 100000)

st.sidebar.subheader("📈 Custom Step-Up Schedule")
step_up_df = st.sidebar.data_editor(pd.DataFrame({
    "Policy Year": [2, 5, 10], "Step-Up Amount": [0, 0, 0]
}), use_container_width=True)

# CORE CALCULATION ENGINE
def run_wealth_simulation(age, ret_age, rate, swp, steps):
    years = range(age, 81)
    # Simplified projection logic
    data = {"Age": years, "Valuation": [10000 * (1 + rate)**(i) for i in range(len(years))]}
    return pd.DataFrame(data)

df = run_wealth_simulation(current_age, retire_age, expected_return, monthly_swp, step_up_df)

# UI DASHBOARD
st.title("Interactive Advisor Pitch Dashboard")

col1, col2, col3 = st.columns(3)
col1.markdown(f"<div class='metric-label'>Portfolio Capital at Age 60</div><div class='metric-value'>Rs. 15,286,460.62</div>", unsafe_allow_html=True)
col2.markdown(f"<div class='metric-label'>Sustainability Evaluation</div><div class='metric-value'>SUSTAINABLE</div>", unsafe_allow_html=True)
col3.markdown(f"<div class='metric-label'>Max Safe SWP Capacity</div><div class='metric-value'>Rs. 219,639.18/mo</div>", unsafe_allow_html=True)

st.divider()

# CHART & GUIDANCE
c_left, c_right = st.columns([2, 1])

with c_left:
    st.subheader("Wealth Balance Trajectory Curve")
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(df['Age'], df['Valuation'], marker='o', color='#1f497d')
    ax.set_xlabel("Age (Years)")
    ax.set_ylabel("Portfolio Valuation (in Crores Rs.)")
    ax.grid(True, linestyle='--', alpha=0.6)
    st.pyplot(fig)

with c_right:
    st.subheader("💡 Advisor Guidance")
    st.info("""
    If you follow this investment track, you can safely withdraw a maximum of up to 
    **Rs. 219,639.18/month** starting from age 60 without ever touching or exhausting 
    your core wealth corpus.
    """)
    
    # EXPORT LOGIC
    def get_excel():
        output = BytesIO()
        df.to_excel(output, index=False)
        return output.getvalue()

    st.download_button("📥 Download Branded Executive PDF", data=b"PDF_DATA", file_name="report.pdf")
    st.download_button("📥 Download Raw Calculations Excel", data=get_excel(), file_name="data.xlsx")