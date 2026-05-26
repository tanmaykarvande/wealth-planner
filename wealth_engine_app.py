"""
Wealth Sustainability Engine — Flet Mobile App
=================================================
Requirements:
    pip install flet pandas

Run (desktop preview):
    python wealth_engine_app.py

Build Android APK:
    flet build apk

Build iOS IPA:
    flet build ipa

Build desktop exe:
    flet build windows   (or macos / linux)
"""

import flet as ft
import math


# ══════════════════════════════════════════════════════════════════════
# 1. PURE CALCULATION ENGINE  (no UI, easily unit-testable)
# ══════════════════════════════════════════════════════════════════════

def calculate_wealth(
    current_age: int,
    swp_start_age: int,
    annual_premium: float,
    monthly_swp: float,
    step_up: float,
) -> dict:
    """
    Projects a 40-year wealth corpus and evaluates SWP sustainability.

    Parameters
    ----------
    current_age    : client's age today
    swp_start_age  : age at which SWP withdrawals begin (retirement age)
    annual_premium : annual insurance / investment premium paid
    monthly_swp    : desired monthly withdrawal after retirement
    step_up        : fixed extra monthly SIP allocation on top of base payout-SIP

    Returns
    -------
    dict with keys:
        corpus_at_retirement  – projected corpus (₹) when SWP starts
        target_needed         – PV of all future SWP withdrawals (₹)
        shortfall             – max(0, target_needed − corpus_at_retirement)
        suggested_fix         – extra ₹/month needed to fully bridge shortfall
        records               – list of dicts [{year, age, corpus, swp_yearly}, …]
    """
    POLICY_TERM    = 40
    PAYOUT_PCT     = 0.40
    ANNUAL_RETURN  = 0.18
    monthly_rate   = ANNUAL_RETURN / 12

    annual_payout  = annual_premium * PAYOUT_PCT
    base_monthly   = annual_payout / 12

    corpus  = 0.0
    records = []

    for year in range(1, POLICY_TERM + 1):
        age        = current_age + (year - 1)
        monthly_sip = base_monthly + step_up
        active_swp  = monthly_swp if age >= swp_start_age else 0.0

        for _ in range(12):
            if corpus < 0:
                corpus = 0.0
            corpus += monthly_sip
            corpus *= (1 + monthly_rate)
            if corpus >= active_swp:
                corpus -= active_swp
            else:
                corpus = 0.0

        records.append({
            "year":       year,
            "age":        age,
            "corpus":     round(corpus, 2),
            "swp_yearly": round(active_swp * 12, 2),
        })

    # Corpus value at the exact retirement year
    ret_rows = [r for r in records if r["age"] == swp_start_age]
    corpus_at_retirement = ret_rows[0]["corpus"] if ret_rows else 0.0

    # Present value of all future SWP withdrawals (annuity formula)
    withdrawal_months = (POLICY_TERM - (swp_start_age - current_age)) * 12
    if withdrawal_months > 0 and monthly_rate > 0:
        pv_factor      = (1 - (1 + monthly_rate) ** -withdrawal_months) / monthly_rate
        target_needed  = round((monthly_swp * pv_factor) / (1 + monthly_rate), 2)
    else:
        target_needed = 0.0

    shortfall = max(0.0, round(target_needed - corpus_at_retirement, 2))

    # Monthly top-up needed to bridge the shortfall (FV of annuity)
    suggested_fix = 0.0
    if shortfall > 0:
        n_months       = (swp_start_age - current_age) * 12
        if n_months > 0:
            annuity_fv    = (((1 + monthly_rate) ** n_months - 1) / monthly_rate) * (1 + monthly_rate)
            suggested_fix = round(shortfall / annuity_fv, 2)

    return {
        "corpus_at_retirement": corpus_at_retirement,
        "target_needed":        target_needed,
        "shortfall":            shortfall,
        "suggested_fix":        suggested_fix,
        "records":              records,
    }


# ══════════════════════════════════════════════════════════════════════
# 2. FORMATTING HELPERS
# ══════════════════════════════════════════════════════════════════════

def fmt_inr(amount: float) -> str:
    """Format a rupee amount with Indian comma grouping."""
    amount = abs(round(amount))
    s = str(amount)
    if len(s) <= 3:
        return f"₹{s}"
    last3   = s[-3:]
    rest    = s[:-3]
    grouped = ""
    while len(rest) > 2:
        grouped = "," + rest[-2:] + grouped
        rest    = rest[:-2]
    grouped = rest + grouped
    return f"₹{grouped},{last3}"


def fmt_lakh(amount: float) -> str:
    return f"{amount / 100_000:.1f} L"


# ══════════════════════════════════════════════════════════════════════
# 3. REUSABLE UI COMPONENTS
# ══════════════════════════════════════════════════════════════════════

TEAL        = "#1D9E75"
TEAL_DARK   = "#0F6E56"
TEAL_LIGHT  = "#E1F5EE"
RED         = "#D85A30"
RED_LIGHT   = "#FAECE7"
BLUE        = "#185FA5"
GREY_BG     = "#F4F6F8"
GREY_BORDER = "#DDE3EA"
WHITE       = "#FFFFFF"
TEXT_MAIN   = "#1A1A1A"
TEXT_MUTED  = "#6B7280"


def input_field(label: str, value: str, ref: ft.Ref, keyboard=ft.KeyboardType.NUMBER) -> ft.Container:
    return ft.Container(
        content=ft.Column(
            [
                ft.Text(label, size=11, color=TEXT_MUTED, weight=ft.FontWeight.W_500),
                ft.TextField(
                    ref=ref,
                    value=value,
                    keyboard_type=keyboard,
                    border_color=GREY_BORDER,
                    focused_border_color=TEAL,
                    bgcolor=WHITE,
                    color=TEXT_MAIN,
                    text_size=14,
                    height=44,
                    content_padding=ft.padding.symmetric(horizontal=12, vertical=8),
                    border_radius=8,
                ),
            ],
            spacing=4,
        ),
        padding=ft.padding.only(bottom=2),
    )


def metric_card(label: str, value_ref: ft.Ref, color: str = TEXT_MAIN) -> ft.Container:
    return ft.Container(
        content=ft.Column(
            [
                ft.Text(label, size=10, color=TEXT_MUTED, weight=ft.FontWeight.W_500),
                ft.Text(ref=value_ref, value="—", size=16, weight=ft.FontWeight.BOLD, color=color),
            ],
            spacing=4,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=WHITE,
        border=ft.border.all(1, GREY_BORDER),
        border_radius=10,
        padding=ft.padding.symmetric(horizontal=12, vertical=12),
        expand=True,
        alignment=ft.alignment.center,
    )


def section_label(text: str) -> ft.Text:
    return ft.Text(
        text.upper(),
        size=11,
        weight=ft.FontWeight.W_600,
        color=TEXT_MUTED,
        letter_spacing=0.8,
    )


# ══════════════════════════════════════════════════════════════════════
# 4. SIMPLE CANVAS BAR CHART  (no external chart lib needed)
# ══════════════════════════════════════════════════════════════════════

class CorpusChart(ft.UserControl):
    """
    A pure-Flet bar chart that draws corpus projection data
    using ft.canvas shapes — no third-party chart library required.
    """

    def __init__(self, height: int = 200):
        super().__init__()
        self._height = height
        self._data: list[dict] = []          # [{age, corpus}, …]
        self._canvas = ft.canvas.Canvas(
            width=float("inf"),
            height=height,
            expand=True,
        )

    def build(self):
        return ft.Container(
            content=self._canvas,
            bgcolor=WHITE,
            border=ft.border.all(1, GREY_BORDER),
            border_radius=10,
            padding=ft.padding.symmetric(horizontal=8, vertical=8),
            height=self._height + 20,
            expand=True,
        )

    def update_data(self, records: list[dict], swp_start_age: int):
        """Redraw chart with new projection records (sampled every 3rd year)."""
        sampled = records[::3]
        self._data = sampled
        self._draw(sampled, swp_start_age)
        self.update()

    def _draw(self, sampled: list[dict], swp_start_age: int):
        import flet.canvas as cv

        shapes = []
        if not sampled:
            self._canvas.shapes = shapes
            return

        max_corpus = max((r["corpus"] for r in sampled), default=1) or 1
        n          = len(sampled)
        chart_h    = self._height - 30   # leave 30px for x-axis labels
        chart_w    = 340                  # reference width; canvas expands
        pad_l, pad_r = 10, 10
        bar_area   = chart_w - pad_l - pad_r
        bar_w      = max(6, bar_area // n - 3)

        for i, rec in enumerate(sampled):
            x       = pad_l + i * (bar_area // n) + (bar_area // n - bar_w) // 2
            ratio   = rec["corpus"] / max_corpus
            bar_h   = max(2, int(ratio * chart_h))
            y_top   = chart_h - bar_h
            color   = TEAL if rec["age"] < swp_start_age else BLUE

            # Bar rectangle
            shapes.append(
                cv.Rect(
                    x=x, y=y_top,
                    width=bar_w, height=bar_h,
                    paint=ft.Paint(color=color, style=ft.PaintingStyle.FILL),
                )
            )

            # X-axis age label (every other bar to avoid crowding)
            if i % 2 == 0:
                shapes.append(
                    cv.Text(
                        x=x + bar_w // 2,
                        y=chart_h + 6,
                        text=str(rec["age"]),
                        style=ft.TextStyle(size=9, color=TEXT_MUTED),
                        alignment=ft.Alignment(0, 0),
                    )
                )

        self._canvas.shapes = shapes


# ══════════════════════════════════════════════════════════════════════
# 5. LEDGER TABLE ROW
# ══════════════════════════════════════════════════════════════════════

def ledger_row(rec: dict, highlight: bool = False) -> ft.DataRow:
    bg = ft.colors.with_opacity(0.04, TEAL) if highlight else None
    return ft.DataRow(
        cells=[
            ft.DataCell(ft.Text(str(rec["year"]), size=12, color=TEXT_MAIN)),
            ft.DataCell(ft.Text(f"{rec['age']} yrs", size=12, color=TEXT_MAIN)),
            ft.DataCell(ft.Text(fmt_inr(rec["swp_yearly"]), size=12, color=BLUE)),
            ft.DataCell(
                ft.Text(fmt_inr(rec["corpus"]), size=12,
                        color=TEAL_DARK, weight=ft.FontWeight.W_600)
            ),
        ],
        color=ft.MaterialStatePropertyAll(bg) if bg else None,
    )


# ══════════════════════════════════════════════════════════════════════
# 6. MAIN APP
# ══════════════════════════════════════════════════════════════════════

def main(page: ft.Page):
    # ── Page config ──────────────────────────────────────────────────
    page.title          = "Wealth Engine"
    page.theme_mode     = ft.ThemeMode.LIGHT
    page.bgcolor        = GREY_BG
    page.padding        = 0
    page.scroll         = ft.ScrollMode.ADAPTIVE

    # Mobile-first sizing; also works on desktop
    page.window_width   = 420
    page.window_height  = 900
    page.fonts          = {}   # use system fonts

    # ── Input refs ───────────────────────────────────────────────────
    ref_name    = ft.Ref[ft.TextField]()
    ref_age     = ft.Ref[ft.TextField]()
    ref_retire  = ft.Ref[ft.TextField]()
    ref_premium = ft.Ref[ft.TextField]()
    ref_swp     = ft.Ref[ft.TextField]()
    ref_step    = ft.Ref[ft.TextField]()

    # ── Output refs ──────────────────────────────────────────────────
    ref_corpus  = ft.Ref[ft.Text]()
    ref_target  = ft.Ref[ft.Text]()
    ref_gap     = ft.Ref[ft.Text]()

    status_text = ft.Text(
        "Adjust parameters and tap Calculate.",
        size=13, color=TEXT_MUTED,
    )
    status_box = ft.Container(
        content=status_text,
        bgcolor=WHITE,
        border=ft.border.all(1, GREY_BORDER),
        border_radius=10,
        padding=ft.padding.symmetric(horizontal=14, vertical=12),
    )

    # ── Chart ────────────────────────────────────────────────────────
    corpus_chart = CorpusChart(height=200)

    # ── Table ────────────────────────────────────────────────────────
    table_header = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Yr",   size=11, weight=ft.FontWeight.W_600, color=TEXT_MUTED)),
            ft.DataColumn(ft.Text("Age",  size=11, weight=ft.FontWeight.W_600, color=TEXT_MUTED)),
            ft.DataColumn(ft.Text("SWP",  size=11, weight=ft.FontWeight.W_600, color=TEXT_MUTED)),
            ft.DataColumn(ft.Text("Corpus", size=11, weight=ft.FontWeight.W_600, color=TEXT_MUTED)),
        ],
        rows=[],
        heading_row_color=ft.colors.with_opacity(0.05, TEAL),
        heading_row_height=36,
        data_row_min_height=34,
        data_row_max_height=34,
        column_spacing=10,
        border=ft.border.all(1, GREY_BORDER),
        border_radius=10,
        expand=True,
    )

    # ── Error snackbar ───────────────────────────────────────────────
    def show_error(msg: str):
        page.snack_bar = ft.SnackBar(
            content=ft.Text(msg, color=WHITE),
            bgcolor=RED,
            duration=3000,
        )
        page.snack_bar.open = True
        page.update()

    # ── Calculate handler ────────────────────────────────────────────
    def on_calculate(e):
        try:
            c_age   = int(ref_age.current.value.strip())
            r_age   = int(ref_retire.current.value.strip())
            premium = float(ref_premium.current.value.strip().replace(",", ""))
            swp     = float(ref_swp.current.value.strip().replace(",", ""))
            step    = float(ref_step.current.value.strip().replace(",", ""))
        except ValueError:
            show_error("Please enter valid numbers in all fields.")
            return

        if r_age <= c_age:
            show_error("Retirement age must be greater than current age.")
            return
        if c_age < 18 or c_age > 80:
            show_error("Current age must be between 18 and 80.")
            return

        result = calculate_wealth(c_age, r_age, premium, swp, step)
        corp   = result["corpus_at_retirement"]
        tgt    = result["target_needed"]
        gap    = result["shortfall"]
        fix    = result["suggested_fix"]
        recs   = result["records"]

        # Update metric cards
        ref_corpus.current.value = fmt_inr(corp)
        ref_target.current.value = fmt_inr(tgt)

        if gap > 0:
            ref_gap.current.value    = "−" + fmt_inr(gap)
            ref_gap.current.color    = RED
            status_text.value        = (
                f"Shortfall identified: {fmt_inr(gap)}\n"
                f"Add {fmt_inr(fix)}/month to bridge the gap completely."
            )
            status_text.color        = "#4A1B0C"
            status_box.bgcolor       = RED_LIGHT
            status_box.border        = ft.border.all(1, "#F0997B")
        else:
            ref_gap.current.value    = "Surplus ✓"
            ref_gap.current.color    = TEAL_DARK
            status_text.value        = "Sustainable portfolio confirmed! Growth easily offsets target withdrawals."
            status_text.color        = "#085041"
            status_box.bgcolor       = TEAL_LIGHT
            status_box.border        = ft.border.all(1, "#5DCAA5")

        # Update chart
        corpus_chart.update_data(recs, r_age)

        # Update table
        table_header.rows.clear()
        for rec in recs:
            highlight = rec["age"] == r_age
            table_header.rows.append(ledger_row(rec, highlight=highlight))

        page.update()

    # ── Layout ───────────────────────────────────────────────────────

    header = ft.Container(
        content=ft.Row(
            [
                ft.Icon(ft.icons.ACCOUNT_BALANCE_WALLET_ROUNDED, color=WHITE, size=22),
                ft.Text("Wealth Engine", size=18, weight=ft.FontWeight.BOLD, color=WHITE),
            ],
            spacing=10,
        ),
        bgcolor=TEAL_DARK,
        padding=ft.padding.symmetric(horizontal=20, vertical=14),
    )

    # Input section
    input_section = ft.Container(
        content=ft.Column(
            [
                section_label("Parameters"),
                ft.Divider(height=1, color=GREY_BORDER),
                input_field("Client Name", "Aditya Sharma", ref_name, ft.KeyboardType.TEXT),
                ft.Row(
                    [
                        ft.Column(
                            [input_field("Current Age", "50", ref_age)],
                            expand=True,
                        ),
                        ft.Column(
                            [input_field("Retirement Age", "60", ref_retire)],
                            expand=True,
                        ),
                    ],
                    spacing=10,
                ),
                input_field("Annual Premium (₹)", "150000", ref_premium),
                input_field("Target Monthly SWP (₹)", "200000", ref_swp),
                input_field("Step-Up Allocation (₹/mo)", "2000", ref_step),
                ft.Container(height=4),
                ft.ElevatedButton(
                    text="Calculate",
                    icon=ft.icons.PLAY_ARROW_ROUNDED,
                    on_click=on_calculate,
                    bgcolor=TEAL,
                    color=WHITE,
                    width=float("inf"),
                    height=48,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=10),
                        elevation=0,
                    ),
                ),
            ],
            spacing=10,
        ),
        bgcolor=WHITE,
        border=ft.border.all(1, GREY_BORDER),
        border_radius=12,
        padding=ft.padding.all(16),
    )

    # Results section
    results_section = ft.Column(
        [
            section_label("Strategy Matrix"),
            ft.Row(
                [
                    metric_card("Corpus at Retirement", ref_corpus, TEAL_DARK),
                    metric_card("Target Needed",        ref_target, TEXT_MAIN),
                    metric_card("Shortfall / Surplus",  ref_gap,    RED),
                ],
                spacing=8,
            ),
            status_box,
            section_label("Portfolio Growth Projection"),
            corpus_chart,
            section_label("Year-over-Year Ledger"),
            ft.Container(
                content=ft.Column(
                    [table_header],
                    scroll=ft.ScrollMode.ALWAYS,
                ),
                border=ft.border.all(1, GREY_BORDER),
                border_radius=10,
                height=340,
            ),
        ],
        spacing=12,
    )

    body = ft.Container(
        content=ft.Column(
            [input_section, results_section],
            spacing=14,
            scroll=ft.ScrollMode.ADAPTIVE,
        ),
        padding=ft.padding.all(14),
    )

    page.add(
        ft.Column(
            [header, body],
            spacing=0,
            scroll=ft.ScrollMode.ADAPTIVE,
            expand=True,
        )
    )


# ══════════════════════════════════════════════════════════════════════
# 7. ENTRY POINT
# ══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    ft.app(target=main)
