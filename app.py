import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from io import BytesIO
import os

# 1. PAGE CONFIG
st.set_page_config(page_title="Wealth Architecture Engine", layout="wide")

# 2. GRANULAR WEALTH ENGINE (Logic preserved from your ledger)
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

# 3. UTILS
def format_inr(val):
    val = int(val)
    s = str(val)
    if len(s) <= 3: return f"Rs. {s}/-"
    last_three = s[-3:]
    other = s[:-3]
    res = ",".join([other[max(0, i-2):i] for i in range(len(other), 0, -2)][::-1])
    return f"Rs. {res},{last_three}/-"

def get_unique_filename(base_name, ext):
    count = 0
    filename = f"{base_name}{ext}"
    while os.path.exists(filename):
        count += 1
        filename = f"{base_name}_{count}{ext}"
    return filename

# 4. EXCEL GENERATOR (Multi-Sheet)
def generate_excel(df, status, client_name):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Sheet 1: Executive Summary
        pd.DataFrame({'Metric': ['Status', 'Terminal Value'], 'Value': [status, df.iloc[-1]['Valuation']]}).to_excel(writer, sheet_name='Executive Summary', index=False)
        # Sheet 2: Annual Projection
        df.to_excel(writer, sheet_name='40-Year Annual Projection', index=False)
        # Sheet 3: Graphs (Placeholder)
        pd.DataFrame({'Info': ['Wealth Trajectory Plot']}).to_excel(writer, sheet_name='Graphs', index=False)
        # Sheet 4: Conditional Deficit Ledger
        if status != "SUSTAINABLE":
            pd.DataFrame({'Analysis': ['MoM Deficit Bridge']}).to_excel(writer, sheet_name='MoM Deficit Bridge Ledger', index=False)
    return output.getvalue()

# 5. UI & EXECUTION
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

val_at_retire = df.loc[df['Age'] == retire_age, 'Valuation'].values[0]
final_val = df.iloc[-1]['Valuation']
status = "SUSTAINABLE" if final_val > 0 else "CORPUS EXHAUSTED"

col1, col2, col3 = st.columns(3)
col1.metric("Capital at Retirement", format_inr(val_at_retire))
col2.metric("Sustainability", status)
col3.metric("Terminal Value (Yr 40)", format_inr(final_val))

# Download Handling
base_filename = f"{client_name}_wealth_management"
st.download_button("📥 Download Excel Report", data=generate_excel(df, status, client_name), file_name=f"{base_filename}.xlsx")
st.button("📥 Download Branded Executive PDF")