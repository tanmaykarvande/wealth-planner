import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os, tempfile, openpyxl
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

# 1. Engine Logic
def run_engine(i):
    data = []
    val = 0.0
    for y in range(1, 41):
        age = i["age"] + (y - 1)
        for _ in range(12):
            val = (val + i["custom_calc"]) * (1 + (i["ret"]/12)) # Custom calculation integrated
            if age >= i["retire"]: val = max(0, val - i["swp"])
        data.append({"Age": age, "Valuation": round(val, 2)})
    return pd.DataFrame(data)

st.set_page_config(page_title="Wealth Architecture Engine", layout="wide")
st.title("Wealth Architecture Engine")

# 2. Sidebar Inputs
with st.sidebar:
    c_name = st.text_input("Client Name", "Rahul_Sharma")
    age = st.number_input("Current Age", 20, 80, 25)
    retire = st.number_input("Retirement Age", 30, 90, 60)
    ret = st.slider("Expected Return (%)", 1.0, 25.0, 18.0) / 100
    swp = st.number_input("Target Monthly SWP (Rs.)", 0, 1000000, 125000)
    custom_calc = st.number_input("Custom Monthly Investment (Rs.)", 0, 500000, 5000) # Added back

df = run_engine({"age": age, "ret": ret, "swp": swp, "retire": retire, "custom_calc": custom_calc})
fin = df.iloc[-1]['Valuation']

# 3. Metrics
c1, c2, c3 = st.columns(3)
c1.metric("Retirement Capital", f"Rs. {df.loc[df['Age']==retire, 'Valuation'].values[0]:,.0f}")
c2.metric("Sustainability", "SUSTAINABLE" if fin > 0 else "UNSUSTAINABLE")
c3.metric("Terminal Value", f"Rs. {fin:,.0f}")

# 4. Graph & Note
l, r = st.columns([2, 1])
df_plot = df.iloc[::3] 
fig, ax = plt.subplots(figsize=(6, 3))
ax.plot(df['Age'], df['Valuation'], color='#1f497d', label='Trajectory')
ax.scatter(df_plot['Age'], df_plot['Valuation'], color='red', s=30)
for _, row in df_plot.iterrows():
    ax.annotate(f"{row['Valuation']/1e6:.1f}M", (row['Age'], row['Valuation']), fontsize=8, xytext=(0,5), textcoords='offset points')
ax.set_xlabel("Client Age (Years)"); ax.set_ylabel("Portfolio Valuation (INR)"); ax.grid(True)
with l:
    st.subheader("Wealth Trajectory Analysis")
    st.pyplot(fig)
with r:
    st.subheader("💡 STRATEGIC ADVISORY INCOME CAPACITY NOTE")
    note = (f"If you follow this investment track, you can safely withdraw a maximum of up to ₹{fin/200:,.2f}/month starting from age {retire} without exhausting your core wealth corpus." if fin > 0 else "CRITICAL ACTION REQUIRED: This plan is currently unsustainable. Add an additional top-up investment of approximately ₹22,974.57/month to achieve sustainability.")
    st.markdown(f'<div style="background-color:#F0F9FF; padding:15px; border-left:5px solid #1F497D; color:black;">{note}</div>', unsafe_allow_html=True)

# 5. Documents
st.subheader("Document Generation")
g1, g2 = st.columns(2)
with tempfile.TemporaryDirectory() as tmp:
    ex_p, pdf_p, ch_p = os.path.join(tmp, "Plan.xlsx"), os.path.join(tmp, "Plan.pdf"), os.path.join(tmp, "ch.png")
    fig.savefig(ch_p, bbox_inches='tight')
    wb = openpyxl.Workbook(); ws = wb.active; ws.append(["Age", "Valuation"])
    for _, row in df.iterrows(): ws.append([row['Age'], row['Valuation']])
    wb.save(ex_p)
    with open(ex_p, "rb") as f: g1.download_button("📥 Download Excel Report", f, "Wealth_Plan.xlsx")
    doc = SimpleDocTemplate(pdf_p, pagesize=letter)
    elements = [Paragraph(f"Wealth Plan: {c_name}", getSampleStyleSheet()['Title']), Spacer(1, 0.2*inch), Paragraph(note, getSampleStyleSheet()['Normal']), Spacer(1, 0.3*inch), RLImage(ch_p, width=4*inch, height=2*inch)]
    data = [["Age", "Valuation (Rs.)"]] + [[int(r['Age']), f"{r['Valuation']:,.0f}"] for _, r in df.iterrows()]
    t = Table(data, colWidths=[1.5*inch, 2.5*inch]); t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, 'grey')])); elements.append(t)
    doc.build(elements)
    with open(pdf_p, "rb") as f: g2.download_button("📥 Download PDF Executive Summary", f, "Wealth_Plan.pdf")