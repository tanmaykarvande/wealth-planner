import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# 1. PAGE CONFIG
st.set_page_config(page_title="Wealth Architecture Engine", layout="wide")

# Indian Number Formatter
def format_indian(val):
    return f"₹{val:,.2f}"

# 2. ENGINE CLASS
class GranularWealthEngine:
    def __init__(self, inputs, step_up_schedule):
        self.annual_premium = 150000
        self.payout_pct = 0.40
        self.base_monthly_sip = round((self.annual_premium * self.payout_pct) / 12, 2)
        self.monthly_rate = inputs["expected_return"] / 12
        self.step_up_schedule = step_up_schedule
        
    def run_projection(self, current_age, swp_start_age, monthly_swp_target):
        records = []
        current_corpus = 0.0
        cumulative_step_up = 0.0
        for year in range(1, 41):
            age = current_age + (year - 1)
            cumulative_step_up += self.step_up_schedule.get(year, 0.0)
            total_monthly_sip = self.base_monthly_sip + cumulative_step_up
            monthly_swp = monthly_swp_target if age >= swp_start_age else 0.0
            for month in range(1, 13):
                current_corpus += total_monthly_sip
                current_corpus *= (1 + self.monthly_rate)
                current_corpus = max(0.0, current_corpus - monthly_swp)
            records.append({"Age": age, "Valuation": round(current_corpus, 2)})
        return pd.DataFrame(records)

# 3. SIDEBAR
st.sidebar.header("📋 Client Parameters")
current_age = st.sidebar.number_input("Current Age", 20, 90, 40)
retire_age = st.sidebar.number_input("Retirement Age", 20, 90, 60)
expected_return = st.sidebar.slider("Expected Return (%)", 1.0, 25.0, 18.0, step=0.05) / 100
monthly_swp = st.sidebar.number_input("Target Monthly SWP (₹)", 0, 1000000, 125000)

st.sidebar.subheader("📅 Step-Up Schedule (Year: Increase)")
schedule_df = st.sidebar.data_editor(pd.DataFrame({"Year": [2, 5, 10], "Increase": [0, 0, 0]}), use_container_width=True)
custom_schedule = dict(zip(schedule_df["Year"], schedule_df["Increase"]))

# 4. EXECUTION
engine = GranularWealthEngine({"expected_return": expected_return}, custom_schedule)
df = engine.run_projection(current_age, retire_age, monthly_swp)

# 5. UI (Small fonts)
st.title("Wealth Indicator Dashboard")
val_at_retire = df.loc[df['Age'] == retire_age, 'Valuation'].values[0]
status = "SUSTAINABLE" if df.iloc[-1]['Valuation'] > 0 else "CORPUS EXHAUSTED"

col1, col2, col3 = st.columns(3)
col1.metric("Capital at Retirement", format_indian(val_at_retire))
col2.metric("Sustainability", status)
col3.metric("Target SWP", format_indian(monthly_swp))

# 6. CHART WITH DATA LABELS
st.subheader("Wealth Trajectory")
fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(df['Age'], df['Valuation'], marker='o', color='#1f497d')

# Labels every 5 years
for i, row in df.iloc[::5].iterrows():
    ax.annotate(f"₹{row['Valuation']/10000000:.1f}Cr", (row['Age'], row['Valuation']), 
                textcoords="offset points", xytext=(0,10), ha='center', fontsize=8)

ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f'₹{x/10000000:.1f}Cr'))
st.pyplot(fig)