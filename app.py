import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os, tempfile, openpyxl
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

# --- BRANDING ---
class WatermarkCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs): super().__init__(*args, **kwargs); self.pages = []
    def showPage(self): self.pages.append(dict(self.__dict__)); self._startPage()
    def save(self):
        for p in self.pages: self.__dict__.update(p); self.draw_wm(); super().save()
        super().save()
    def draw_wm(self):
        self.saveState(); self.setFont("Helvetica-Bold", 38); self.setFillColor(colors.HexColor("#E5E7EB")); self.setFillAlpha(0.12)
        self.translate(4.25*inch, 5.5*inch); self.rotate(45); self.drawCentredString(0, 0, "Livlong Insurance Brokers Limited"); self.restoreState()

# --- ENGINE ---
def run_engine(inputs):
    records = []
    val = 0.0
    for year in range(1, 41):
        age = inputs["current_age"] + (year - 1)
        for _ in range(12):
            val = (val + 5000) * (1 + (inputs["expected_return"]/12))
            if age >= inputs["swp_start_age"]: val = max(0, val - inputs["monthly_swp"])
        records.append({"Age": age, "Valuation": round(val, 2)})
    return pd.DataFrame(records)

# --- UI ---
st.set_page_config(page_title="Wealth Architecture Engine", layout="wide")
st.title("Wealth Architecture Engine")

# Sidebar
c_name = st.sidebar.text_input("Client Name", "Rahul_Sharma")
c_age = st.sidebar.number_input("Current Age", 20, 80, 25)
s_age = st.sidebar.number_input("Retirement Age", 30, 90, 60)
ret = st.sidebar.slider("Expected Return (%)", 1.0, 25.0, 18.0) / 100
swp = st.sidebar.number_input("Target Monthly SWP (Rs.)", 0, 1000000, 125000)

inputs = {"current_age": c_age, "expected_return": ret, "monthly_swp": swp, "swp_start_age": s_age}
df = run_engine(inputs)
fin_val = df.iloc[-1]['Valuation']

# Metrics
c1, c2, c3 = st.columns(3)
c1.metric("Capital at Retirement", f"Rs. {df.loc[df['Age'] == s_age, 'Valuation'].values[0]:,.0f}")
c2.metric("Sustainability", "SUSTAINABLE" if fin_val > 0 else "UNSUSTAINABLE")
c3.metric("Terminal Value", f"Rs. {fin_val:,.0f}")

# Chart
st.subheader("Wealth Trajectory Analysis")
fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(df['Age'], df['Valuation'], marker='o', color='#1f497d')
ax.set_xlabel("Age"); ax.set_ylabel("Portfolio Valuation (Rs.)"); ax.grid(True)
st.pyplot(fig)

# Advisor Note
st.subheader("💡 STRATEGIC ADVISORY INCOME CAPACITY NOTE")
note = (f"If you follow this investment track, you can safely withdraw a maximum of up to ₹{fin_val/200:,.2f}/month (₹{(fin_val/200)*12:,.2f}/year) starting from age {s_age} without ever touching or exhausting your core wealth corpus." 
        if fin_val > 0 else "CRITICAL ACTION REQUIRED: This plan is currently unsustainable. Please adjust parameters.")
st.markdown(f'<div style="background-color:#F0F9FF; padding:15px; border-left:5px solid #1F497D; color:black;">{note}</div>', unsafe_allow_html=True)

# Generators
st.subheader("Document Generation")
col_a, col_b = st.columns(2)
with tempfile.TemporaryDirectory() as tmp:
    ex_path, pdf_path, chart_path = os.path.join(tmp, "Plan.xlsx"), os.path.join(tmp, "Summary.pdf"), os.path.join(tmp, "chart.png")
    fig.savefig(chart_path)
    
    # Excel Generation
    wb = openpyxl.Workbook(); ws = wb.active; ws.append(["Age", "Valuation"])
    for _, row in df.iterrows(): ws.append([row['Age'], row['Valuation']])
    wb.save(ex_path)
    with open(ex_path, "rb") as f: col_a.download_button("📥 Download Excel Report", f, "Wealth_Plan.xlsx")
    
    # PDF Generation
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    elements = [Paragraph(f"Wealth Plan: {c_name}", getSampleStyleSheet()['Title']), Spacer(1, 0.2*inch), Paragraph(note, getSampleStyleSheet()['Normal']), Spacer(1, 0.3*inch), RLImage(chart_path, width=5*inch, height=2.5*inch)]
    data = [["Age", "Valuation (Rs.)"]] + [[int(r['Age']), f"{r['Valuation']:,.0f}"] for _, r in df.iterrows()]
    t = Table(data, colWidths=[1.5*inch, 3*inch]); t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey)])); elements.append(t)
    doc.build(elements, canvasmaker=WatermarkCanvas)
    with open(pdf_path, "rb") as f: col_b.download_button("📥 Download PDF Executive Summary", f, "Wealth_Plan.pdf")