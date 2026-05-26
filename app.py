import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import tempfile
import openpyxl
import urllib.request
from io import BytesIO
from openpyxl.drawing.image import Image
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

# --- PAGE CONFIG ---
st.set_page_config(page_title="Wealth Architecture Engine", layout="wide")

# --- ENGINE ---
class GranularWealthEngine:
    def __init__(self, inputs):
        self.current_age = inputs["current_age"]
        self.expected_return = inputs["expected_return"]
        self.monthly_swp_target = inputs["monthly_swp"]
        self.swp_start_age = inputs["swp_start_age"]
        self.base_monthly_sip = 5000.00
    
    def run_projection(self):
        records = []
        current_corpus = 0.0
        for year in range(1, 41):
            age = self.current_age + (year - 1)
            swp = self.monthly_swp_target if age >= self.swp_start_age else 0.0
            for month in range(1, 13):
                current_corpus += self.base_monthly_sip
                current_corpus *= (1 + (self.expected_return / 12))
                if age >= self.swp_start_age: current_corpus = max(0.0, current_corpus - swp)
            records.append({"Age": age, "Valuation": round(current_corpus, 2)})
        return pd.DataFrame(records)

# --- PDF MODULE ---
class WatermarkCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs); self.pages = []
    def showPage(self):
        self.pages.append(dict(self.__dict__)); self._startPage()
    def save(self):
        for page in self.pages:
            self.__dict__.update(page); self.draw_watermark(); super().showPage()
        super().save()
    def draw_watermark(self):
        self.saveState(); self.setFont("Helvetica-Bold", 38); self.setFillColor(colors.HexColor("#E5E7EB")); self.setFillAlpha(0.12)
        self.translate(4.25 * inch, 5.5 * inch); self.rotate(45); self.drawCentredString(0, 0, "Livlong Insurance Brokers Limited"); self.restoreState()

def generate_client_pdf(inputs, summary_data, chart_path, pdf_filename, is_unsustainable, bridge_val, max_swp):
    doc = SimpleDocTemplate(pdf_filename, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    story = []
    base_styles = getSampleStyleSheet()
    PRIMARY_COLOR = colors.HexColor("#1F497D")
    
    # Header
    company_header_style = ParagraphStyle('CompHeader', parent=base_styles['Normal'], fontName='Helvetica-Bold', fontSize=12, textColor=PRIMARY_COLOR, alignment=2)
    company_name_p = Paragraph("<b>Livlong Insurance Brokers Limited</b><br/><font size=8 color='#555555'>Wealth Advisory Division</font>", company_header_style)
    header_table = Table([["", company_name_p]], colWidths=[3.75 * inch, 3.75 * inch])
    story.append(header_table)
    
    # Content
    story.append(Paragraph("STRATEGIC WEALTH ARCHITECTURE PLAN", ParagraphStyle('Title', parent=base_styles['Normal'], fontName='Helvetica-Bold', fontSize=22, textColor=PRIMARY_COLOR)))
    
    if os.path.exists(chart_path):
        story.append(RLImage(chart_path, width=7.5 * inch, height=3.75 * inch))
        
    doc.build(story, canvasmaker=WatermarkCanvas)

# --- UI LAYER ---
st.title("Wealth Architecture Engine")
client_name = st.sidebar.text_input("Client Name", "Rahul_Sharma")
current_age = st.sidebar.number_input("Current Age", 20, 80, 25)
retire_age = st.sidebar.number_input("Retirement Age", 30, 90, 60)
expected_return = st.sidebar.slider("Expected Return (%)", 1.0, 25.0, 18.0) / 100
monthly_swp = st.sidebar.number_input("Target Monthly SWP (Rs.)", 0, 1000000, 125000)

advisor_inputs = {"client_name": client_name, "current_age": current_age, "expected_return": expected_return, "monthly_swp": monthly_swp, "swp_start_age": retire_age}
engine = GranularWealthEngine(advisor_inputs)
projection_matrix = engine.run_projection()

# Metrics/Display
val_at_retire = projection_matrix.loc[projection_matrix['Age'] == retire_age, 'Valuation'].values[0]
final_val = projection_matrix.iloc[-1]['Valuation']
is_unsustainable = final_val <= 0

col1, col2, col3 = st.columns(3)
col1.metric("Capital at Retirement", f"Rs. {val_at_retire:,.0f}")
col2.metric("Sustainability", "UNSUSTAINABLE" if is_unsustainable else "SUSTAINABLE")
col3.metric("Terminal Value", f"Rs. {final_val:,.0f}")

fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(projection_matrix['Age'], projection_matrix['Valuation'], marker='o')
st.pyplot(fig)

# --- GENERATION ---
if st.button("Generate Final Executive Docs"):
    with tempfile.TemporaryDirectory() as tmp_dir:
        excel_path = os.path.join(tmp_dir, "Wealth_Plan.xlsx")
        pdf_path = os.path.join(tmp_dir, "Execution_Summary.pdf")
        chart_path = os.path.join(tmp_dir, "chart1.png")
        fig.savefig(chart_path)
        
        # Excel Logic
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Executive Summary"
        ws.cell(row=1, column=1, value="Wealth Plan for " + client_name)
        wb.save(excel_path)
        
        # PDF Logic
        summary = {"Client": client_name, "Sustainability": "Fail" if is_unsustainable else "Pass"}
        generate_client_pdf(advisor_inputs, summary, chart_path, pdf_path, is_unsustainable, 1000, 50000)
        
        with open(excel_path, "rb") as f: st.download_button("Download Excel", f, "Wealth_Plan.xlsx")
        with open(pdf_path, "rb") as f: st.download_button("Download PDF", f, "Execution_Summary.pdf")
        st.success("Documents generated.")