# /// script
# dependencies = [
#   "numpy",
#   "pandas",
#   "streamlit",
#   "reportlab",
#   "matplotlib",
# ]
# ///

# ═════════════════════════════════════════════════════════════════════════════════════════
# 📋 1. IMPORT REQUIRED LIBRARIES
# ═════════════════════════════════════════════════════════════════════════════════════════
import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import urllib.request
from io import BytesIO

# ReportLab libraries for building the PDF
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

# ═════════════════════════════════════════════════════════════════════════════════════════
# ⚙️ 2. CORE CALCULATION ENGINES
# ═════════════════════════════════════════════════════════════════════════════════════════

class GranularWealthEngine:
    def __init__(self, inputs: dict, step_up_schedule: dict):
        self.client_name = inputs.get("client_name", "Valued Client")
        self.current_age = inputs.get("current_age", 35)
        self.annual_premium = inputs.get("annual_premium", 150000)
        self.payout_pct = inputs.get("payout_pct", 0.40)
        self.life_cover_multiple = inputs.get("life_cover_multiple", 7)
        self.ppt = inputs.get("ppt", 12)
        self.policy_term = inputs.get("policy_term", 40)
        self.expected_return = inputs.get("expected_return", 0.18)
        self.monthly_swp_target = inputs.get("monthly_swp", 100000)
        self.swp_start_age = inputs.get("swp_start_age", 60)
        self.step_up_schedule = step_up_schedule
        
        self.life_cover = self.annual_premium * self.life_cover_multiple
        self.annual_payout = self.annual_premium * self.payout_pct
        self.base_monthly_sip = round(self.annual_payout / 12, 2)
        self.monthly_rate = self.expected_return / 12
        
    def run_projection(self, alternative_swp_age: int = None, custom_swp_target: float = None) -> pd.DataFrame:
        target_swp_age = alternative_swp_age if alternative_swp_age is not None else self.swp_start_age
        active_swp_payout = custom_swp_target if custom_swp_target is not None else self.monthly_swp_target
        
        records = []
        current_corpus = 0.0
        cumulative_step_up = 0.0
        
        for year in range(1, self.policy_term + 1):
            age = self.current_age + (year - 1)
            premium_paid = self.annual_premium if year <= self.ppt else 0.0
            insurance_payout = self.annual_payout
            
            year_specific_increment = self.step_up_schedule.get(year, 0.0)
            cumulative_step_up += year_specific_increment
            
            total_monthly_sip = self.base_monthly_sip + cumulative_step_up
            annual_sip_contribution = total_monthly_sip * 12
            monthly_swp = active_swp_payout if age >= target_swp_age else 0.0
            
            for month in range(1, 13):
                if current_corpus <= 0: current_corpus = 0.0
                current_corpus += total_monthly_sip
                current_corpus *= (1 + self.monthly_rate)
                
                if current_corpus >= monthly_swp: current_corpus -= monthly_swp
                else: current_corpus = 0.0
            
            net_corpus = round(current_corpus, 2)
            annual_swp_withdrawn = (active_swp_payout * 12) if age >= target_swp_age else 0.0
            status = "Corpus Exhausted" if net_corpus <= 0 else "Sustainable"
                
            records.append({
                "Policy Year": year, "Age": age, "Premium Paid (₹)": premium_paid,
                "Insurance Payout (₹)": insurance_payout, "Base Monthly SIP (₹)": self.base_monthly_sip,
                "New Step-Up Added (₹)": year_specific_increment, "Total Monthly SIP (₹)": total_monthly_sip,
                "Annual SIP Contribution (₹)": annual_sip_contribution, "Annual SWP Withdrawal (₹)": annual_swp_withdrawn,
                "Net End-of-Year Corpus (₹)": net_corpus, "Sustainability Flag": status
            })
        return pd.DataFrame(records)

    def generate_executive_summary(self, df: pd.DataFrame, max_monthly_swp: float, suggested_topup: float = 0.0) -> dict:
        retirement_row = df[df["Age"] == self.swp_start_age]
        corpus_at_retirement = retirement_row["Net End-of-Year Corpus (₹)"].values[0] if not retirement_row.empty else 0.0
        final_corpus = df["Net End-of-Year Corpus (₹)"].iloc[-1]
        
        remaining_years = self.policy_term - (self.swp_start_age - self.current_age)
        n_months = max(0, remaining_years * 12)
        r_monthly = self.monthly_rate
        required_corpus = self.monthly_swp_target * ((1 - (1 + r_monthly)**-n_months) / r_monthly) if n_months > 0 else 0.0
            
        exhausted_rows = df[df["Sustainability Flag"] == "Corpus Exhausted"]
        survival_status = "Corpus Exhausted" if not exhausted_rows.empty else "Sustainable"
        survives_until_year = exhausted_rows["Policy Year"].values[0] if not exhausted_rows.empty else self.policy_term
        survives_until_age = exhausted_rows["Age"].values[0] if not exhausted_rows.empty else self.current_age + self.policy_term
            
        if survival_status == "Sustainable":
            max_annual_equivalent = max_monthly_swp * 12
            formatted_strategic_note = (
                f"If you follow this investment track, you can safely withdraw a maximum of up to "
                f"₹{max_monthly_swp:,.2f}/month (₹{max_annual_equivalent:,.2f}/year) starting from age {self.swp_start_age} "
                f"without ever touching or exhausting your core wealth corpus."
            )
        else:
            formatted_strategic_note = (
                f"CRITICAL ACTION REQUIRED: This plan is currently unsustainable. To meet your target milestone, "
                f"you need to add an additional top-up investment of approximately ₹{suggested_topup:,.2f}/month "
                f"on top of the standard payouts from the policy to transition this framework into a fully sustainable model."
            )
            
        return {
            "Life Cover Amount": self.life_cover, "Monthly Insurance Payout": self.base_monthly_sip,
            "Corpus at SWP Start": corpus_at_retirement, "Target Required Corpus": round(required_corpus, 2),
            "Surplus / Shortfall": round(corpus_at_retirement - required_corpus, 2), "Final Year 40 Corpus": final_corpus,
            "Sustainability Status": survival_status, "Years Corpus Survives": survives_until_year,
            "Age Corpus Exhausted": survives_until_age, "Client Presentation Note": formatted_strategic_note
        }

    def predict_sustainability_gap(self, df: pd.DataFrame) -> dict:
        retirement_year_row = df[df["Age"] == self.swp_start_age]
        actual_corpus_at_start = 0.0
        if not retirement_year_row.empty:
            target_policy_year = retirement_year_row["Policy Year"].values[0]
            prior_row = df[df["Policy Year"] == (target_policy_year - 1)]
            actual_corpus_at_start = prior_row["Net End-of-Year Corpus (₹)"].values[0] if not prior_row.empty else 0.0

        remaining_years = self.policy_term - (self.swp_start_age - self.current_age)
        total_withdrawal_months = max(0, remaining_years * 12)
        
        r = self.monthly_rate
        exact_target_needed = (self.monthly_swp_target * ((1 - (1 + r) ** -total_withdrawal_months) / r)) / (1 + r) if r > 0 and total_withdrawal_months > 0 else 0.0
        shortfall = round(max(0.0, exact_target_needed - actual_corpus_at_start), 2)
        return {"Target Needed": round(exact_target_needed, 2), "Shortfall": shortfall}

    def calculate_inflection_point(self, df: pd.DataFrame) -> tuple:
        gap_info = self.predict_sustainability_gap(df)
        target_needed = gap_info["Target Needed"]
        for _, row in df.iterrows():
            if row["Age"] < self.swp_start_age:
                months_to_retirement = (self.swp_start_age - row["Age"]) * 12
                discounted_safety_target = target_needed / ((1 + self.monthly_rate) ** months_to_retirement)
                if row["Net End-of-Year Corpus (₹)"] < discounted_safety_target:
                    return int(row["Policy Year"]), int(row["Age"])
        return 1, self.current_age

    def find_max_monthly_swp_for_zero_residual(self) -> float:
        low_bound, high_bound, tolerance = 0.0, 10000000.0, 0.01
        best_payout = 0.0
        for _ in range(100):
            mid_payout = (low_bound + high_bound) / 2.0
            test_df = self.run_projection(custom_swp_target=mid_payout)
            if (test_df["Sustainability Flag"] == "Corpus Exhausted").iloc[:-1].any() or (test_df["Net End-of-Year Corpus (₹)"].iloc[-1] <= 0 and test_df["Net End-of-Year Corpus (₹)"].iloc[-1] == 0.0):
                high_bound = mid_payout
            else:
                best_payout = mid_payout
                low_bound = mid_payout
            if abs(high_bound - low_bound) < tolerance: break
        return round(best_payout, 2)

class DeficitBridgeEngine:
    def __init__(self, target_gap: float, start_age: int, target_age: int, expected_return: float):
        self.total_months = max(0, (target_age - start_age) * 12)
        r = expected_return / 12
        if self.total_months > 0 and r > 0:
            annuity_factor = (((1 + r) ** self.total_months - 1) / r) * (1 + r)
            self.required_monthly_investment = round(target_gap / annuity_factor, 2)
        else:
            self.required_monthly_investment = 0.0

# ═════════════════════════════════════════════════════════════════════════════════════════
# 🎨 3. BACKGROUND CANVAS FOR EXECUTIVE PDF EXPORT
# ═════════════════════════════════════════════════════════════════════════════════════════
class WatermarkCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pages = []
    def showPage(self):
        self.pages.append(dict(self.__dict__))
        self._startPage()
    def save(self):
        for page in self.pages:
            self.__dict__.update(page)
            self.draw_watermark()
            super().showPage()
        super().save()
    def draw_watermark(self):
        self.saveState()
        self.setFont("Helvetica-Bold", 36)
        self.setFillColor(colors.HexColor("#E5E7EB")) 
        self.setFillAlpha(0.12)
        self.translate(4.25 * inch, 5.5 * inch)
        self.rotate(45)
        self.drawCentredString(0, 0, "Livlong Insurance Brokers Limited")
        self.restoreState()

def generate_client_pdf(inputs: dict, summary_data: dict, chart_path: str):
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    story = []
    
    PRIMARY_COLOR = colors.HexColor("#1F497D")
    TEXT_COLOR = colors.HexColor("#222222")
    ACCENT_RED = colors.HexColor("#9C0006")
    ACCENT_GREEN = colors.HexColor("#006100")
    BG_LIGHT = colors.HexColor("#F9FAFB")
    
    base_styles = getSampleStyleSheet()
    title_style = ParagraphStyle('T', fontName='Helvetica-Bold', fontSize=18, textColor=PRIMARY_COLOR, leading=22, spaceAfter=4)
    subtitle_style = ParagraphStyle('S', fontName='Helvetica', fontSize=11, textColor=colors.HexColor("#444444"), leading=14, spaceAfter=15)
    company_style = ParagraphStyle('C', fontName='Helvetica-Bold', fontSize=11, textColor=PRIMARY_COLOR, alignment=2, leading=13)
    section_heading = ParagraphStyle('H', fontName='Helvetica-Bold', fontSize=12, textColor=PRIMARY_COLOR, spaceBefore=10, spaceAfter=6)
    body_style = ParagraphStyle('B', fontName='Helvetica', fontSize=9.5, textColor=TEXT_COLOR, leading=13)
    t_head_style = ParagraphStyle('TH', fontName='Helvetica-Bold', fontSize=9.5, textColor=colors.white, alignment=1)
    advice_style = ParagraphStyle('A', fontName='Helvetica-Oblique', fontSize=10, textColor=PRIMARY_COLOR, leading=15)

    logo_text = Paragraph("<b>LIVLONG INSURANCE</b>", body_style)
    company_name_p = Paragraph("<b>Livlong Insurance Brokers Limited</b><br/><font size=7.5 color='#555555'>Wealth Advisory Division</font>", company_style)
    header_table = Table([[logo_text, company_name_p]], colWidths=[3.75 * inch, 3.75 * inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('ALIGN', (0,0), (0,0), 'LEFT'), ('ALIGN', (1,0), (1,0), 'RIGHT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6), ('LINEBELOW', (0,0), (-1,-1), 1, colors.HexColor("#E5E7EB")),
    ]))
    
    story.append(header_table)
    story.append(Spacer(1, 10))
    story.append(Paragraph("STRATEGIC WEALTH ARCHITECTURE PLAN", title_style))
    story.append(Paragraph(f"<b>Client Profile:</b> {inputs['client_name']}  |  <b>Confidential Portfolio Forecast</b>", subtitle_style))
    
    story.append(Paragraph("Key Model Assessment Metrics", section_heading))
    is_red = summary_data["Sustainability Status"] == "Corpus Exhausted"
    status_color = ACCENT_RED if is_red else ACCENT_GREEN
    
    kpi_rows = [
        [Paragraph("<b>Financial Vector Variable</b>", t_head_style), Paragraph("<b>Target Valuation Metrics</b>", t_head_style)],
        [Paragraph("Current Age", body_style), Paragraph(f"{inputs['current_age']} Years", body_style)],
        [Paragraph("Expected Portfolio Returns", body_style), Paragraph(f"{inputs['expected_return']*100:.1f}% Annualized", body_style)],
        [Paragraph("Target Retirement Milestone Age", body_style), Paragraph(f"{inputs['swp_start_age']} Years Old", body_style)],
        [Paragraph("Initial Monthly Insurance Payout Stream", body_style), Paragraph(f"₹ {summary_data['Monthly Insurance Payout']:,.2f}", body_style)],
        [Paragraph("Total Guaranteed Life Cover Amount", body_style), Paragraph(f"₹ {summary_data['Life Cover Amount']:,.2f}", body_style)],
        [Paragraph(f"Accumulated Capital at Age {inputs['swp_start_age']}", body_style), Paragraph(f"₹ {summary_data['Corpus at SWP Start']:,.2f}", body_style)],
        [Paragraph("Required Corpus Target for Target SWP", body_style), Paragraph(f"₹ {summary_data['Target Required Corpus']:,.2f}", body_style)],
        [Paragraph("Calculated Surplus / Shortfall Gap", body_style), Paragraph(f"₹ {summary_data['Surplus / Shortfall']:,.2f}", body_style)],
        [Paragraph("Strategy Sustainability Status", body_style), Paragraph(f"<b>{summary_data['Sustainability Status'].upper()}</b>", ParagraphStyle('St', parent=body_style, textColor=status_color, fontName='Helvetica-Bold'))],
    ]
    
    metrics_table = Table(kpi_rows, colWidths=[4.0 * inch, 3.5 * inch])
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), PRIMARY_COLOR), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4), ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT]), ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
    ]))
    story.append(metrics_table)
    
    story.append(Paragraph("Strategic Advisory Commentary", section_heading))
    note_p = Paragraph(f"💡 <b>Advisor Analysis Note:</b><br/>{summary_data['Client Presentation Note']}", advice_style)
    note_box = Table([[note_p]], colWidths=[7.5 * inch])
    note_box.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor("#EFF6FF")), ('BOX', (0, 0), (0, 0), 1, colors.HexColor("#BFDBFE")),
        ('PADDING', (0, 0), (0, 0), 10),
    ]))
    story.append(note_box)
    
    story.append(PageBreak())
    story.append(header_table)
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("Long-Term Wealth Projection Mapping", section_heading))
    story.append(Spacer(1, 10))
    if os.path.exists(chart_path):
        story.append(RLImage(chart_path, width=7.5 * inch, height=3.5 * inch))
        
    doc.build(story, canvasmaker=WatermarkCanvas)
    pdf_buffer.seek(0)
    return pdf_buffer

# ═════════════════════════════════════════════════════════════════════════════════════════
# 💻 4. INTERACTIVE USER INTERFACE DESIGN (STREAMLIT)
# ═════════════════════════════════════════════════════════════════════════════════════════
st.set_page_config(page_title="Livlong Wealth Architecture Engine", layout="wide")

st.sidebar.header("📋 Client Parameter Profile")
c_name = st.sidebar.text_input("Client Name", "Rahul Sharma")

# Upper max_value bound completely removed to prevent scaling blocks
c_age = st.sidebar.number_input("Current Age", min_value=18, value=25)

# Dynamic fallback anchor that shifts default initialization to clear ValueBelowMinError
smart_default_retirement = max(int(c_age) + 5, 50) 
retire_age = st.sidebar.number_input(
    "Target Retirement Milestone Age", 
    min_value=int(c_age) + 1, 
    value=smart_default_retirement
)

exp_return = st.sidebar.slider("Expected Portfolio Return (%)", min_value=1.0, max_value=25.0, value=18.0, step=0.5) / 100

st.sidebar.subheader("💰 Strategy Goals")
target_monthly_swp = st.sidebar.number_input("Target Monthly SWP (₹)", value=350000, step=10000)

# Custom absolute currency top-up step up schedule safely preserved
custom_schedule = {
    2: 500,
    5: 1000
}

# Consolidated Input Profile Data
advisor_inputs = {
    "client_name": c_name,     
    "current_age": int(c_age),
    "annual_premium": 150000,
    "payout_pct": 0.40,
    "life_cover_multiple": 7,
    "ppt": 12,
    "policy_term": 40,
    "expected_return": exp_return, 
    "monthly_swp": target_monthly_swp,      
    "swp_start_age": int(retire_age)
}

engine = GranularWealthEngine(advisor_inputs, custom_schedule)
max_sustainable_monthly_swp = engine.find_max_monthly_swp_for_zero_residual()
projection_matrix = engine.run_projection()

top_up_start_year, top_up_start_age = engine.calculate_inflection_point(projection_matrix)
gap_analysis = engine.predict_sustainability_gap(projection_matrix)
GAP_AMOUNT = gap_analysis["Shortfall"]
bridge_calculator = DeficitBridgeEngine(GAP_AMOUNT, top_up_start_age, engine.swp_start_age, engine.expected_return)

summary = engine.generate_executive_summary(projection_matrix, max_sustainable_monthly_swp, bridge_calculator.required_monthly_investment)

# UI Elements Matrix Layout
st.title("LIVLONG WEALTH ARCHITECTURE ENGINE")
st.markdown("### Interactive Advisor Pitch Dashboard")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label=f"Portfolio Capital at Age {retire_age}", value=f"₹{summary['Corpus at SWP Start']:,.2f}")
with col2:
    st.metric(label="Sustainability Evaluation", value=summary['Sustainability Status'].upper())
with col3:
    if summary['Sustainability Status'] == "Corpus Exhausted":
        st.metric(label="Required Monthly Top-Up", value=f"₹{bridge_calculator.required_monthly_investment:,.2f}")
    else:
        st.metric(label="Max Safe SWP Capacity", value=f"₹{max_sustainable_monthly_swp:,.2f}/mo")

# Curve projection plotting loop
fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(projection_matrix["Age"], projection_matrix["Net End-of-Year Corpus (₹)"] / 10000000, color="#1F497D", linewidth=2.5)
ax.fill_between(projection_matrix["Age"], projection_matrix["Net End-of-Year Corpus (₹)"] / 10000000, color="#1F497D", alpha=0.1)
ax.set_title("Wealth Balance Trajectory Curve")
ax.set_xlabel("Age (Years)")
ax.set_ylabel("Portfolio Valuation (in Crores ₹)")
ax.grid(True, linestyle="--", alpha=0.5)
chart_img_path = "temp_chart.png"
plt.savefig(chart_img_path, bbox_inches='tight', dpi=150)
plt.close()

main_col1, main_col2 = st.columns([1.3, 0.7])
with main_col1:
    # Upgraded parameter: use_container_width -> width='stretch' to eliminate layout warnings
    st.image(chart_img_path, width="stretch")
with main_col2:
    st.subheader("💡 Advisor Guidance")
    st.info(summary['Client Presentation Note'])
    
    pdf_data = generate_client_pdf(advisor_inputs, summary, chart_img_path)
    
    # Modernized layout parameters for interactive action components
    st.download_button(
        label="📥 Download Branded Executive PDF",
        data=pdf_data,
        file_name=f"{c_name.replace(' ', '_')}_Wealth_Architecture_Plan.pdf",
        mime="application/pdf",
        width="stretch"
    )