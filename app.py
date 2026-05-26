import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# 1. PAGE CONFIG
st.set_page_config(page_title="Wealth Architecture Engine", layout="wide")

# 2. GRANULAR WEALTH ENGINE CLASS
class GranularWealthEngine:
    def __init__(self, inputs, step_up_schedule):
        self.current_age = inputs.get("current_age", 40)
        self.annual_premium = 150000
        self.payout_pct = 0.40
        self.expected_return = inputs.get("expected_return", 0.18)
        self.monthly_swp_target = inputs.get("monthly_swp", 125000)
        self.swp_start_age = inputs.get("swp_start_age", 60)
        self.base_monthly_sip = round((self.annual_premium * self.payout_pct) / 12, 2)
        self.monthly_rate = self.expected_return / 12
        self.step_up_schedule = step_up_schedule
        
    def run_projection(self):
        records = []
        current_corpus = 0.0
        cumulative_step_up = 0.0
        for year in range(1, 41):
            age = self.current_age + (year - 1)
            cumulative_step_up += self.step_up_schedule.get(year, 0.0)
            total_monthly_sip = self.base_monthly_sip + cumulative_step_up
            monthly_swp = self.monthly_swp_target if age >= self.swp_start_age else 0.0
            for month in range(1, 13):
                current_corpus += total_monthly_sip
                current_corpus *= (1 + self.monthly_rate)
                current_corpus = max(0.0, current_corpus - monthly_swp)
            records.append({"Age": age, "Valuation": round(current_corpus, 2)})
        return pd.DataFrame(records)

# 3. INDIAN FORMATTER (XX,XX,XX,XXX/-)
def format_inr(val):
    val = int(val)
    s = str(val)
    if len(s) <= 3: return f"Rs. {s}/-"
    last_three = s[-3:]
    other = s[:-3]
    res = ",".join([other[max(0, i-2):i] for i in range(len(other), 0, -2)][::-1])
    return f"Rs. {res},{last_three}/-"

# 4. SIDEBAR INPUTS
st.sidebar.header("📋 Client Parameter Profile")
client_name = st.sidebar.text_input("Client Name", "Aditya Sharma")
current_age = st.sidebar.number_input("Current Age", 20, 80, 40)
retire_age = st.sidebar.number_input("Retirement Age", 30, 90, 60)
expected_return = st.sidebar.slider("Expected Portfolio Return (%)", 1.0, 25.0, 18.0, step=0.05) / 100
monthly_swp = st.sidebar.number_input("Target Monthly SWP (Rs.)", 0, 1000000, 125000)

st.sidebar.subheader("📈 Custom Step-Up Schedule")
schedule_df = st.sidebar.data_editor(pd.DataFrame({"Year": [2, 5, 10], "Increase": [0, 0, 0]}), use_container_width=True)
custom_schedule = dict(zip(schedule_df["Year"], schedule_df["Increase"]))

# 5. EXECUTION
engine = GranularWealthEngine({
    "current_age": current_age, 
    "expected_return": expected_return, 
    "monthly_swp": monthly_swp, 
    "swp_start_age": retire_age
}, custom_schedule)
df = engine.run_projection()

# 6. DASHBOARD UI
st.title("Wealth Indicator Dashboard")
val_at_retire = df.loc[df['Age'] == retire_age, 'Valuation'].values[0]
status = "SUSTAINABLE" if df.iloc[-1]['Valuation'] > 0 else "CORPUS EXHAUSTED"

col1, col2, col3 = st.columns(3)
col1.metric("Capital at Retirement", format_inr(val_at_retire))
col2.metric("Sustainability", status)
col3.metric("Target Monthly SWP", format_inr(monthly_swp))

st.divider()

# 7. CHART & ADVISOR GUIDANCE
c_left, c_right = st.columns([2, 1])
with c_left:
    st.subheader("Wealth Balance Trajectory")
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df['Age'], df['Valuation'], marker='o', color='#1f497d', linewidth=2)
    # 5-year labels
    for i, row in df.iloc[::5].iterrows():
        ax.annotate(f"Rs.{row['Valuation']/10000000:.1f} Cr", (row['Age'], row['Valuation']), 
                    textcoords="offset points", xytext=(0,10), ha='center', fontsize=9)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f'Rs.{x/10000000:.2f} Cr'))
    ax.grid(True, linestyle='--', alpha=0.6)
    st.pyplot(fig)

with c_right:
    st.subheader("💡 Advisor Guidance")
    final_corpus = df.iloc[-1]['Valuation']
    if status == "SUSTAINABLE":
        safe_monthly = (val_at_retire * (expected_return / 1.5)) / 12 
        st.success(f"**STRATEGIC ADVISORY INCOME CAPACITY NOTE:**\n\n"
                   f"If you follow this investment track, you can safely withdraw a maximum of up to "
                   f"**{format_inr(safe_monthly)}/month** starting from age {retire_age} "
                   f"without ever touching or exhausting your core wealth corpus.")
    else:
        shortfall = abs(final_corpus) / 40 / 12 
        st.error(f"**CRITICAL ACTION REQUIRED:**\n\n"
                 f"This plan is currently unsustainable. To meet your target milestone, you need "
                 f"to add an additional top-up investment of approximately "
                 f"**{format_inr(shortfall)}/month** on top of your standard payouts to transition "
                 f"this framework into a fully sustainable model.")
    
    st.write("")
    st.button("📥 Download Branded Executive PDF")
    st.button("📥 Download Raw Calculations Excel")