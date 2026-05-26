import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from io import BytesIO
import os

# 1. PAGE CONFIG
st.set_page_config(page_title="Wealth Architecture Engine", layout="wide")

# 2. GRANULAR WEALTH ENGINE (Matches your ledger logic)
class GranularWealthEngine:
    def __init__(self, inputs, step_up_schedule):
        self.current_age = inputs.get("current_age", 25)
        self.expected_return = inputs.get("expected_return", 0.18)
        self.monthly_swp_target = inputs.get("monthly_swp", 125000)
        self.swp_start_age = inputs.get("swp_start_age", 60)
        self.base_monthly_sip = 5000.00
        self.monthly_rate = self.expected_return / 12
        self.step_up_schedule = step_up_schedule
        
    def run_projection(self):
        records = []
        current_corpus = 0.0
        cumulative_step_up = 0.0
        for year in range(1, 41):
            age = self.current_age + (year - 1)
            cumulative_step_up += self.step_up_schedule.get(year, 0.0)
            total_sip = self.base_monthly_sip + cumulative_step_up
            swp = self.monthly_swp_target if age >= self.swp_start_age else 0.0
            for month in range(1, 13):
                current_corpus += total_sip
                current_corpus *= (1 + self.monthly_rate)
                if age >= self.swp_start_age: current_corpus = max(0.0, current_corpus - swp)
            records.append({"Age": age, "Valuation": round(current_corpus, 2)})
        return pd.DataFrame(records)

# 3. UTILS & FORMATTERS
def format_inr(val):
    val = int(val)
    s = str(val)
    if len(s) <= 3: return f"Rs. {s}/-"
    last_three = s[-3:]
    other = s[:-3]
    res = ",".join([other[max(0, i-2):i] for i in range(len(other), 0, -2)][::-1])
    return f"Rs. {res},{last_three}/-"

# 4. EXCEL GENERATOR (Multi-Sheet Professional)
def generate_excel(df, status, client_name):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        pd.DataFrame({'Metric': ['Status', 'Terminal Value'], 'Value': [status, df.iloc[-1]['Valuation']]}).to_excel(writer, sheet_name='Executive Summary', index=False)
        df.to_excel(writer, sheet_name='40-Year Annual Projection', index=False)
        pd.DataFrame({'Visual Anchors': ['Wealth Trajectory Plot']}).to_excel(writer, sheet_name='Graphs', index=False)
        if status != "SUSTAINABLE":
            pd.DataFrame({'Analysis': ['MoM Deficit Bridge Data']}).to_excel(writer, sheet_name='MoM Deficit Bridge Ledger', index=False)
        
        # Style Headers
        workbook = writer.book
        header_fmt = workbook.add_format({'bold': True, 'bg_color': '#1f497d', 'font_color': 'white'})
        for sheetname in writer.sheets:
            worksheet = writer.sheets[sheetname]
            for col_num, value in enumerate(writer.sheets[sheetname].table_columns if hasattr(writer.sheets[sheetname], 'table_columns') else []):
                worksheet.write(0, col_num, value, header_fmt)
    return output.getvalue()

# 5. UI
st.title("Wealth Indicator Dashboard")
client_name = st.sidebar.text_input("Client Name", "Rahul_Sharma")
current_age = st.sidebar.number_input("Current Age", 20, 80, 25)
retire_age = st.sidebar.number_input("Retirement Age", 30, 90, 60)
expected_return = st.sidebar.slider("Expected Return (%)", 1.0, 25.0, 18.0, step=0.05) / 100
monthly_swp = st.sidebar.number_input("Target Monthly SWP (Rs.)", 0, 1000000, 125000)
schedule_df = st.sidebar.data_editor(pd.DataFrame({"Year": [2, 5, 10], "Increase": [0, 0, 0]}), use_container_width=True)
custom_schedule = dict(zip(schedule_df["Year"], schedule_df["Increase"]))

engine = GranularWealthEngine({"current_age": current_age, "expected_return": expected_return, "monthly_swp": monthly_swp, "swp_start_age": retire_age}, custom_schedule)
df = engine.run_projection()

# 6. METRICS
val_at_retire = df.loc[df['Age'] == retire_age, 'Valuation'].values[0]
final_val = df.iloc[-1]['Valuation']
status = "SUSTAINABLE" if final_val > 0 else "CORPUS EXHAUSTED"

col1, col2, col3 = st.columns(3)
col1.metric("Capital at Retirement", format_inr(val_at_retire))
col2.metric("Sustainability Status", status)
col3.metric("Terminal Value (Yr 40)", format_inr(final_val))

st.divider()

# 7. CHART & ADVISORY
c_left, c_right = st.columns([2, 1])
with c_left:
    st.subheader("Wealth Balance Trajectory")
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(df['Age'], df['Valuation'], marker='o', color='#1f497d', linewidth=2.5)
    for i, row in df.iloc[::3].iterrows(): # 3-Year Interval Labels
        ax.annotate(f"₹{row['Valuation']/10000000:.1f}Cr", (row['Age'], row['Valuation']), xytext=(0,10), textcoords='offset points', ha='center', fontsize=9, fontweight='bold')
    ax.set_xlabel("Age of Client (Years)", fontweight='bold')
    ax.set_ylabel("Portfolio Valuation (Rs. in Crores)", fontweight='bold')
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f'₹{x/10000000:.1f} Cr'))
    ax.grid(True, linestyle='--', alpha=0.6)
    st.pyplot(fig)

with c_right:
    st.subheader("💡 Advisor Guidance")
    if status == "SUSTAINABLE":
        safe = (val_at_retire * (expected_return / 12)) 
        st.success(f"**STRATEGIC ADVISORY INCOME CAPACITY NOTE:**\n\nYou can safely withdraw **{format_inr(safe)}/month** starting from age {retire_age} without exhausting your core corpus.")
    else:
        short = abs(final_val) / 40 / 12 
        st.error(f"**CRITICAL ACTION REQUIRED:**\n\nPlan is not sustainable. A top-up of **{format_inr(short)}/month** to is required to reach sustainability.")
    
    st.download_button("📥 Download Excel Report", data=generate_excel(df, status, client_name), file_name=f"{client_name}_wealth_management.xlsx")
    st.button("📥 Download Branded Executive PDF")