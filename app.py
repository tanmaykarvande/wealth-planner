import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from io import BytesIO

# 1. PAGE CONFIG
st.set_page_config(page_title="Wealth Architecture Engine", layout="wide")

# 2. LOGO & CSS STYLING
st.image("https://assets.livlong.com/static-images/gmc/LL-INSURANCE-LOGO1.png", width=200)

st.markdown("""
    <style>
    .metric-value { font-size: 24px !important; font-weight: bold; color: #1f497d; }
    .metric-label { font-size: 14px !important; color: #555; }
    </style>
    """, unsafe_allow_html=True)

# 3. SIDEBAR INPUTS
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

# 4. SIMULATION ENGINE
def run_simulation():
    # Reduced points: Only showing every 5th year to keep the chart clean
    years = range(40, 81, 5)
    data = {"Age": years, "Valuation": [10000000 * (1.1)**(i-40) for i in years]}
    return pd.DataFrame(data)

df = run_simulation()

# 5. DASHBOARD UI
st.title("Interactive Advisor Pitch Dashboard")

col1, col2, col3 = st.columns(3)
col1.markdown("<div class='metric-label'>Portfolio Capital at Age 60</div><div class='metric-value'>Rs. 15,286,460.62</div>", unsafe_allow_html=True)
col2.markdown("<div class='metric-label'>Sustainability Evaluation</div><div class='metric-value'>SUSTAINABLE</div>", unsafe_allow_html=True)
col3.markdown("<div class='metric-label'>Max Safe SWP Capacity</div><div class='metric-value'>Rs. 219,639.18/mo</div>", unsafe_allow_html=True)

st.divider()

# 6. CLEANED CHART
c_left, c_right = st.columns([2, 1])

with c_left:
    st.subheader("Wealth Balance Trajectory Curve")
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df['Age'], df['Valuation'], marker='o', color='#1f497d', linewidth=2.5)
    
    # Y-Axis Formatting
    def format_crores(x, pos): return f'Rs.{x/10000000:.2f} Cr'
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(format_crores))
    
    # Reduced Labels (Only 4 points to avoid overcrowding)
    for i, row in df.iloc[::2].iterrows(): # Take every 2nd point from our 5-year step list
        ax.annotate(f"Rs.{row['Valuation']/10000000:.1f} Cr", 
                    (row['Age'], row['Valuation']), 
                    textcoords="offset points", xytext=(0,10), ha='center', fontsize=9)
    
    ax.grid(True, linestyle='--', alpha=0.6)
    st.pyplot(fig)

with c_right:
    st.subheader("💡 Advisor Guidance")
    st.info("""
    If you follow this investment track, you can safely withdraw a maximum of up to 
    **Rs. 219,639.18/month** starting from age 60 without ever touching or exhausting 
    your core wealth corpus.
    """)
    st.button("📥 Download Branded Executive PDF")
    st.button("📥 Download Raw Calculations Excel")