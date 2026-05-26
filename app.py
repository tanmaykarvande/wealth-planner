import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os, tempfile
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

# 1. Engine
def run_engine(i):
    data = []
    val = 0.0
    for y in range(1, 41):
        age = i["age"] + (y - 1)
        for _ in range(12):
            val = (val + i["custom_calc"]) * (1 + (i["ret"]/12))
            if age >= i["retire"]: val = max(0, val - i["swp"])
        data.append({"Age": age, "Valuation": round(val, 2)})
    return pd.DataFrame(data)

st.set_page_config(page_title="Wealth Engine", layout="wide")
st.title("Wealth Architecture Engine")

# 2. Sidebar
with st.sidebar:
    c_name = st.text_input("Client Name", "Rahul_Sharma")
    age = st.number_input("Current Age", 20, 80, 25)
    retire = st.number_input("Retirement Age", 30, 90, 60)
    ret = st.slider("Expected Return (%)", 1.0, 25.0, 18.0) / 100
    swp = st.number_input("Monthly SWP (Rs.)", 0, 1000000, 125000)
    custom_calc = st.number_input("Monthly Investment (Rs.)", 0, 500000, 5000)

df = run_engine({"age": age, "ret": ret, "swp": swp, "retire": retire, "custom_calc": custom_calc})
fin = df.iloc[-1]['Valuation']

# 3. Visuals & Note
l, r = st.columns([2, 1])
df_plot = df.iloc[::3]
fig, ax = plt.subplots(figsize=(6, 3))
ax.plot(df['Age'], df['Valuation'], color='#1f497d')
ax.scatter(df_plot['Age'], df_plot['Valuation'], color='red', s=20)
for _, row in df_plot.iterrows():
    ax.annotate(f"{row['Valuation']/1e6:.1f}M", (row['Age'], row['Valuation']), fontsize=7, xytext=(0,5), textcoords='offset points')
ax.set_xlabel("Client Age"); ax.set_ylabel("INR"); ax.grid(True)
with l: st.pyplot(fig)
with r:
    note = f"If you follow this track, you can safely withdraw ₹{fin/200:,.2f}/month from age {retire}."
    st.markdown(f'<div style="background:#F0F9FF; padding:15px; border-left:5px solid #1F497D; color:black;">{note}</div>', unsafe_allow_html=True)

# 4. Professional Document Generation
st.subheader("Document Generation")
g1, g2 = st.columns(2)
with tempfile.TemporaryDirectory() as tmp:
    ex_p, pdf_p, ch_p = os.path.join(tmp, "Plan.xlsx"), os.path.join(tmp, "Plan.pdf"), os.path.join(tmp, "ch.png")
    fig.savefig(ch_p, bbox_inches='tight')
    
    # PRO Excel (XlsxWriter)
    with pd.ExcelWriter(ex_p, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Projection', index=False)
        workbook = writer.book; worksheet = writer.sheets['Projection']
        fmt = workbook.add_format({'num_format': '#,##0'})
        worksheet.set_column('B:B', 15, fmt)
    with open(ex_p, "rb") as f: g1.download_button("📥 Download Pro Excel", f, "Wealth_Plan.xlsx")
    
    # PRO PDF
    doc = SimpleDocTemplate(pdf_p, pagesize=letter)
    style = getSampleStyleSheet()
    elems = [Paragraph("Wealth Executive Summary", style['Title']), Spacer(1, 0.2*inch), RLImage(ch_p, width=4*inch, height=2*inch), Spacer(1, 0.2*inch)]
    data = [["Age", "Valuation (INR)"]] + [[int(r['Age']), f"{r['Valuation']:,.0f}"] for _, r in df.iterrows()]
    t = Table(data, colWidths=[1.5*inch, 2*inch])
    t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, 'grey'), ('BACKGROUND', (0,0), (-1,0), '#1f497d'), ('TEXTCOLOR', (0,0), (-1,0), 'white')]))
    elems.append(t)
    doc.build(elems)
    with open(pdf_p, "rb") as f: g2.download_button("📥 Download Pro PDF", f, "Wealth_Plan.pdf")