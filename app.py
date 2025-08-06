#Custom License for S.R.A.

#Copyright (c) 2025 Jacob W. Klingman

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objs as go
import numpy_financial as npf
from fpdf import FPDF
import os, json
import requests

from datetime import datetime

st.set_page_config(
    page_title="RentIntel",
    page_icon="favicon.png",  
    layout="wide"
)

def sanitize_text(text):
    if text:
       
        text = text.replace("🏠", "[House]")
    return text

def portfolio_pdf(df, filename="portfolio_summary.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, latin1("Portfolio Summary"), ln=True)
    pdf.ln(2)

    pdf.set_font("Arial", "", 12)
    total_cf = float(df["Cash Flow ($/yr)"].sum())
    avg_roi = df["ROI (%)"].mean(skipna=True)
    avg_cap = df["Cap Rate (%)"].mean(skipna=True)
    n_props = len(df)

    pdf.cell(0, 8, latin1(f"Properties: {n_props}"), ln=True)
    pdf.cell(0, 8, latin1(f"Total Annual Cash Flow: ${total_cf:,.0f}"), ln=True)
    if not np.isnan(avg_roi):
        pdf.cell(0, 8, latin1(f"Average ROI: {avg_roi:.1f}%"), ln=True)
    if not np.isnan(avg_cap):
        pdf.cell(0, 8, latin1(f"Average Cap Rate: {avg_cap:.1f}%"), ln=True)

    pdf.ln(4)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, latin1("Properties"), ln=True)
    pdf.set_font("Arial", "", 11)

    for _, r in df.iterrows():
        title = r.get("Property", "-")
        cf = float(r.get("Cash Flow ($/yr)", 0.0) or 0.0)
        roi = r.get("ROI (%)", np.nan)
        cap = r.get("Cap Rate (%)", np.nan)
        sc  = r.get("Score", np.nan)

        
        pdf.cell(0, 7, latin1(f"- {title}"), ln=True)

        line = f"   CF: ${cf:,.0f}/yr"
        if not pd.isna(roi):
            line += f"  |  ROI: {float(roi):.1f}%"
        if not pd.isna(cap):
            line += f"  |  Cap: {float(cap):.1f}%"
        if not pd.isna(sc):
            line += f"  |  Score: {float(sc):.1f}"

        pdf.cell(0, 7, latin1(line), ln=True)

    pdf.output(filename)
    return filename


def comparison_to_pdf(df, filename="property_comparison.pdf", preferred_ttf="DejaVuSansCondensed.ttf"):
    """
    Create a Property Comparison PDF from a DataFrame with columns:
      "Property Name", "Purchase Price", "Monthly Rent", "Monthly Expenses",
      "Cash Flow", "Cap Rate", "ROI", "Score"

    - Uses a Unicode TTF font if available (recommended).
    - Falls back to Arial (latin-1) and uses hyphens instead of bullets in fallback mode.
    - Returns the output filename.
    """
    from fpdf import FPDF
    import os
    import math

    def ensure_unicode_font(pdf: FPDF, ttf_path: str):
        """
        Try to register a Unicode TTF; return (font_name, unicode_ok).
        On fallback, sets Arial (core) and returns ('Arial', False).
        """
        if os.path.exists(ttf_path):
            try:
                pdf.add_font('DejaVu', '', ttf_path, uni=True)
                pdf.set_font('DejaVu', '', 12)
                return ('DejaVu', True)
            except Exception:
                pass
        pdf.set_font('Arial', '', 12)
        return ('Arial', False)

    def fmt_value(key, val):
        """Consistent formatting for numbers by key."""
        if val is None or (isinstance(val, float) and math.isnan(val)):
            return "-"
        if key in ("Cap Rate", "ROI"):
            try:
                return f"{float(val):.1f}%"
            except Exception:
                return str(val)
        if key == "Score":
            try:
                return f"{float(val):.1f}"
            except Exception:
                return str(val)
        if key in ("Purchase Price", "Monthly Rent", "Monthly Expenses", "Cash Flow"):
            try:
                return f"${float(val):,.2f}"
            except Exception:
                return str(val)
        return str(val)

    pdf = FPDF()
    pdf.set_auto_page_break(auto=False)  
    pdf.add_page()
    font_name, unicode_ok = ensure_unicode_font(pdf, preferred_ttf)

    pdf.set_font(font_name if unicode_ok else 'Arial', 'B', 16)
    pdf.cell(0, 10, "Property Comparison Report", ln=True)
    pdf.ln(4)

    pdf.set_font(font_name if unicode_ok else 'Arial', '', 10)

    keys = [
        "Purchase Price", "Monthly Rent", "Monthly Expenses",
        "Cash Flow", "Cap Rate", "ROI", "Score"
    ]

    def maybe_sanitize(text):
        
        try:
            return sanitize_text(text)
        except NameError:
            return text

    
    def maybe_page_break(min_space_needed=40):
        if pdf.get_y() > (297 - 10 - min_space_needed):  
            pdf.add_page()
            
            if unicode_ok:
                pdf.set_font(font_name, '', 10)
            else:
                pdf.set_font('Arial', '', 10)

   
    for _, row in df.iterrows():
        maybe_page_break(min_space_needed=48)

        prop_name = row.get("Property Name", "-")
        prop_name = maybe_sanitize(str(prop_name))

        pdf.set_fill_color(240, 240, 240)
        bullet = "• " if unicode_ok else "- "
        pdf.set_font(font_name if unicode_ok else 'Arial', 'B', 11)
        pdf.cell(0, 8, f"{bullet}{prop_name}", ln=True, fill=True)

        pdf.set_font(font_name if unicode_ok else 'Arial', '', 10)
        for key in keys:
            val = row.get(key, "-")
            disp = fmt_value(key, val)
            pdf.cell(60, 8, f"{key}:", border=0)
            pdf.cell(0, 8, str(maybe_sanitize(disp)), ln=True)

        pdf.ln(3)

    pdf.output(filename)
    return filename



st.markdown("""
<script>
  function detectDevice() {
      let width = window.innerWidth;
      if (width <= 768) {
          document.body.classList.add('mobile');
          document.body.classList.remove('desktop');
      } else {
          document.body.classList.add('desktop');
          document.body.classList.remove('mobile');
      }
  }

  window.addEventListener('resize', detectDevice);
  window.onload = detectDevice;
</script>
""", unsafe_allow_html=True)

def export_csv_with_watermark(df):
    watermark = f"# Exported by RentIntel on {datetime.now().strftime('%Y-%m-%d')}\n"
    return (watermark + df.to_csv(index=False)).encode()

WATERMARK_TEXT = "RentIntel – Smart Rental Analyzer"


if "deals" not in st.session_state:
    if os.path.exists("deals.json"):
        with open("deals.json", "r") as f:
            st.session_state["deals"] = json.load(f)
    else:
        st.session_state["deals"] = []

def plot_dual_line_chart(title, x_vals, y1_vals, y1_name, y2_vals, y2_name):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x_vals, y=y1_vals, mode='lines+markers', name=y1_name))
    fig.add_trace(go.Scatter(x=x_vals, y=y2_vals, mode='lines+markers', name=y2_name))
    fig.update_layout(
        title=title,
        xaxis_title='Year',
        yaxis_title='Amount ($)',
        template='plotly_white'
    )
    return fig

# ─────────────────────────── PAGE CONFIG ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title=" RentIntel", layout="wide")

# ─────────────────────────── GLOBAL STYLING ─────────────────────────────────────────────────────────────────────────────────────────────────
custom_css = """
<style>
:root {
  --bg: #18181b;
  --surface: #232326;
  --text: #f3f3f3;
  --accent: #4ade80;
  --thumb: #9c27b0;
  --radius: 1rem;
  --shadow: 0 4px 10px rgba(0,0,0,0.35);
}

/* Page background */
body { background-color: var(--bg); }

/* Block padding */
section.main > div { padding: 1.75rem !important; }

/* Card container */
.card {
  background: var(--surface);
  border-radius: var(--radius);
  padding: 1.25rem 1.5rem;
  margin-bottom: 1.5rem;
  box-shadow: var(--shadow);
  color: var(--text);
}

/* Headings */
h1, h2, h3 { color: var(--text); margin-top: 1rem; margin-bottom: .5rem; }

/* Sliders */
[data-testid="stSlider"] .rc-slider-rail { background: var(--accent)20 !important; }
[data-testid="stSlider"] .rc-slider-track { background: var(--accent) !important; }
[data-testid="stSlider"] .rc-slider-handle { background: var(--thumb) !important; border:2px solid #fff !important; box-shadow:0 0 0 3px var(--thumb)40 !important; }

/* Buttons */
.stButton>button { background: var(--accent); color:#000; border-radius:8px; }

/* Number inputs */
input, textarea { background:#2a2a2a !important; color: var(--text) !important; border-radius:6px !important; }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)


# ── Sticky Deal Summary Bar ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
def render_summary_bar(title, items):
    rows = "".join([
        f"<div style='flex:1 1 200px;padding:0.25rem 1rem;'>"
        f"<div style='color:#bbb;font-size:14px'>{label}</div>"
        f"<div style='font-size:20px;font-weight:600;color:#fff'>{value}</div>"
        f"</div>"
        for label, value in items
    ])
    html = (
        f"<div style='background:#232326;padding:0.75rem 1rem;border-radius:12px;margin-bottom:1.25rem;"
        f"box-shadow:0 2px 10px rgba(0,0,0,0.4);display:flex;flex-wrap:wrap;justify-content:space-between;'>"
        f"<h4 style='flex:1 100%;color:#fff;margin-bottom:0.5rem'>{title}</h4>"
        f"{rows}"
        f"</div>"
    )
    st.markdown(html, unsafe_allow_html=True)


# ─────────────────────────── TOOLTIP HELPER ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────
TOOLTIP = """
<span class='tooltip'>[?]<span class='tooltiptext'>{}</span></span>
"""


def tt(label:str, tip:str):
    return f"**{label}** {TOOLTIP.format(tip)}"

# ─────────────────────────── HEADER / NAV ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
st.markdown("<h1 style='text-align:center;'>🏡 Smart Rental Analyzer</h1>", unsafe_allow_html=True)
col_l, col_c, col_r = st.columns([2.2,2,0.8])
with col_c: st.image("logo.png", width=200)
st.markdown("<p style='text-align:center; font-size:14px; color:gray;'></p>", unsafe_allow_html=True)


st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
if st.button("👋 Quick Deal Analyzer Tutorial"):
    st.session_state.page_redirect = "👋 Get Started"
    st.rerun()
st.markdown("</div>", unsafe_allow_html=True)




st.markdown("### 📬 Contact Me")
st.markdown("**Email:** [smart-rental-analyzer@outlook.com](mailto:smart-rental-analyzer@outlook.com)")
st.markdown("""
Welcome to RentIntel! Here's a quick overview of what the app offers.  
For more advanced guides and tips, check out the link below:

[🔗 Quick Guide: How to Use RentIntel - Full Tutorial](https://rentintel-quick-guide.netlify.app/)
""", unsafe_allow_html=True)



if "page_redirect" in st.session_state:
    st.session_state.page = st.session_state.pop("page_redirect")

if "page" not in st.session_state:
    st.session_state.page = "🏠 Home"  



page = st.selectbox("Navigate to:", [
    "🏠 Home",
    "👋 Get Started",
    "📊 Quick Deal Analyzer",
    "👥 Tenant Affordability Tool",
    "💡 Break-Even Calculator",
    "📘 Multi-Year ROI + Tax Insights",
    "🏘 Property Comparison",
    "📑 Lender Package",
    "📊 Portfolio Dashboard",
    "📂 Deal History",
    "🧪 Advanced Analytics",
    "📈 Monte Carlo Simulator",
    "🏚 Rehab & Refi",
    "💸 Tax Benefits",
    "📖 Help & Info"
], index=[
    "🏠 Home",
    "👋 Get Started",
    "📊 Quick Deal Analyzer",
    "👥 Tenant Affordability Tool",
    "💡 Break-Even Calculator",
    "📘 Multi-Year ROI + Tax Insights",
    "🏘 Property Comparison",
    "📑 Lender Package",
    "📊 Portfolio Dashboard",
    "📂 Deal History",
    "🧪 Advanced Analytics",
    "📈 Monte Carlo Simulator",
    "🏚 Rehab & Refi",
    "💸 Tax Benefits",
    "📖 Help & Info"
].index(st.session_state.page), key="page")




def plot_line_chart(title, x_vals, y_dict):
    fig = go.Figure()
    for label, values in y_dict.items():
        fig.add_trace(go.Scatter(x=x_vals, y=values, mode='lines+markers', name=label))
    fig.update_layout(
        title=title,
        plot_bgcolor="#18181b",
        paper_bgcolor="#18181b",
        font_color="#f3f3f3",
        xaxis=dict(title="", gridcolor="#333"),
        yaxis=dict(title="", gridcolor="#333"),
        margin=dict(l=30, r=30, t=40, b=30)
    )
    return fig


# ─────────────────────────── HOME ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
if page == "🏠 Home":
    st.markdown("---")
    st.markdown("<div class='card'>", unsafe_allow_html=True)

    cols = st.columns(3)
    cols[0].success("✅ Beginner Friendly")
    cols[1].info("📈 Advanced ROI Tools")
    cols[2].warning("💾 Export & Reports")

    st.markdown("---")
    st.markdown("**Features:** Quick Deal Analyzer, ROI & Projections, Break-Even, CSV/PDF Exports, Premium Pro tools")
    st.markdown("Disclaimer: This tool is for educational and estimation purposes only. Always consult a qualified professional (real estate agent, CPA, lender) before making investment decisions.")
    st.markdown("---")


    st.markdown("### 🆚 How We Stack Up Against Competitors")

    comp_data = {
        'Feature': [
            'Quick Deal Analyzer',
            'Multi-Year ROI + Tax Insights',
            'Break-Even Calculator',
            'Property Comparison (Manual + Auto)',
            'Portfolio Dashboard (Aggregated Metrics)',
            'Advanced Analytics (Scenarios)',
            'Monte Carlo Simulator',
            'Rehab & Refi Tools',
            'Tenant Affordability Tool',
            'Tax Benefits Explorer',
            'Deal History & Snapshots',
            'Score System (0–100 w/ Tips)',
            'CSV Export',
            'PDF Export',
            'Mobile Friendly / PWA'
        ],
        'RentIntel': ['✅'] * 15,
        'BiggerPockets': [
            '✅', '✅', '❌', '❌', '❌', '❌', '❌', '❌', '❌',
            '❌', '❌', '❌', '✅', '❌', '✅'
        ],
        'Stessa': [
            '❌', '✅', '❌', '❌', '❌', '❌', '❌', '✅', '❌',
            '✅', '❌', '❌', '✅', '❌', '✅'
        ],
        'Roofstock': [
            '✅', '✅', '❌', '❌', '❌', '❌', '❌', '❌', '❌',
            '❌', '❌', '❌', '✅', '✅', '✅'
        ],
        'DealCheck': [
            '✅', '✅', '❌', '✅', '❌', '❌', '❌', '❌', '❌',
            '❌', '❌', '❌', '✅', '❌', '🚧'
        ],
        'Mashvisor': [
            '✅', '✅', '❌', '❌', '✅', '❌', '❌', '❌', '❌',
            '❌', '❌', '❌', '✅', '❌', '✅'
        ],
        'Rentometer': [
            '✅', '❌', '❌', '❌', '❌', '❌', '❌', '❌', '❌',
            '❌', '❌', '❌', '❌', '❌', '✅'
        ],
        'Zilculator': [
            '✅', '✅', '✅', '✅', '❌', '❌', '❌', '❌', '❌',
            '❌', '❌', '❌', '✅', '❌', '❌'
        ]
    }


    styled = pd.DataFrame(comp_data).set_index('Feature')
    st.dataframe(styled, use_container_width=True)


elif page == "👋 Get Started":
    st.markdown("<div class='card'>", unsafe_allow_html=True)

    if "wizard_step" not in st.session_state:
        st.session_state.wizard_step = 1
        st.session_state.wizard_data = {}

    step = st.session_state.wizard_step
    data = st.session_state.wizard_data

    if step == 1:
        st.header("👋 Welcome to RentInel's Smart Rental Analyzer!")
        st.markdown("---")
        st.markdown("**Features:** Quick Deal Analyzer, ROI & Projections, Break-Even, CSV/PDF Exports, Premium Pro tools")
        st.markdown("---")
        
       
        st.markdown("### 🧑‍🏫 **How This Works**")
    st.markdown("""
This app helps you analyze rental deals, compare properties, project returns, and understand financial impact — even without an API or outside data source.

---

### 🔍 Core Tools

#### 📊 **Quick Deal Analyzer**
- **Purpose**: Quickly evaluate a rental deal with basic inputs.
- **Outputs**: ROI, Cap Rate, Cash Flow, and a 0–100 Score.
- **Extras**: Automatic tags (🔥 Hot Lead, etc.), suggestions, and a donut chart of monthly expenses.

#### 💡 **Break-Even Calculator**
- **Purpose**: Find the minimum rent needed to break even.
- **Outputs**: Estimated break-even rent and cash flow chart.
- **Why It Matters**: Helps you avoid cash-negative deals.

#### 📘 **Multi-Year ROI + Tax Insights**
- **Purpose**: Forecast performance over 1–30 years.
- **Outputs**: Cash-on-cash ROI, equity growth, tax savings, IRR.
- **Extras**: Assumptions are editable; includes pie chart of monthly expenses and CSV exports.

---

### 🔧 Advanced Planning

#### 🧪 **Advanced Analytics**
- **Purpose**: Model different scenarios (conservative to aggressive).
- **Outputs**: Year-by-year cash flow, ROI, and IRR projections.
- **Why It Helps**: Test how different strategies affect returns.

#### 📈 **Monte Carlo Simulator**
- **Purpose**: Run 100–2000 randomized simulations.
- **Outputs**: Distribution of ROI and IRR based on rent, expenses, appreciation ranges.
- **Why It Helps**: See best- and worst-case outcomes.

#### 🏚 **Rehab & Refi Tools**
- **Purpose**: Estimate ROI from renovations or refinancing.
- **Outputs**: Post-rehab equity, refi loan terms, cash-out amounts.
- **Why It Helps**: Decide if adding value or pulling cash out is worth it.

---

### 📋 Comparison & Tracking

#### 🏘 **Property Comparison**
- **Purpose**: Compare multiple deals side-by-side.
- **Outputs**: ROI, Cap Rate, Cash Flow, and custom score for each.
- **Why It Helps**: Choose the best deal based on numbers.

#### 📂 **Deal History**
- **Purpose**: Save & revisit your past deals.
- **Extras**: Filter by tags or status, delete old ones, export grouped summaries to PDF.
- **Includes**: Monthly expense breakdowns added to exports.

#### 📊 **Deal Summary Comparison**
- **Purpose**: Compare saved deals using emojis & metrics.
- **Outputs**: Score, ROI, Cap Rate, and Cash Flow indicators.
- **Why It Helps**: Fast visual comparison of your top choices.

---

### 👥 Screening & Affordability

#### 👥 **Tenant Affordability Tool**
- **Purpose**: Determine required income for a rent, or max rent for an income.
- **Why It Helps**: Screen tenants or reverse-engineer target rents.
- **Extras**: Adjustable rent-to-income ratio and period type.

---

### 📚 Education & Help

#### 💸 **Tax Benefits**
- **Purpose**: Learn what landlord tax deductions you qualify for.
- **Includes**: IRS links, write-off tips, and audit-readiness advice.
- **Why It Helps**: Keep more of your rental income.

#### 📖 **Help & Info**
- **Purpose**: Understand key real estate terms and how the app works.
- **Includes**: Definitions, explanations, and methodology for all calculations.

---
### ✅ Suggested First Steps
1. Run a deal through **📊 Quick Deal Analyzer**
2. Use **📘 Multi-Year ROI** to see long-term potential
3. Save the deal and compare it in **📂 Deal History**
4. Use **👥 Tenant Affordability Tool** to estimate target tenant profile
5. Explore other tools as needed
""")



    st.markdown("""
This 3-step wizard helps you analyze your first rental deal with zero stress.

Click **Next** to begin.
        """)
    if st.button("➡️ Next"):
        st.session_state.wizard_step += 1
        st.rerun()
        


    elif step == 2:
        st.header("🏠 Step 1: Property Inputs")
        data["name"] = st.text_input("Property Name", value=data.get("name", "Untitled Deal"))
        data["price"] = st.number_input("Purchase Price ($)", value=data.get("price", 250000))
        data["rent"] = st.number_input("Expected Monthly Rent ($)", value=data.get("rent", 2200))
        data["expenses"] = st.number_input("Estimated Monthly Expenses ($)", value=data.get("expenses", 1400))
        data["down"] = st.slider("Down Payment (%)", 0, 100, data.get("down", 20))

        col1, col2 = st.columns(2)
        if col1.button("⬅️ Back"):
            st.session_state.wizard_step -= 1
            st.rerun()

        if col2.button("➡️ Analyze"):
            st.session_state.wizard_step += 1
            st.rerun()


    elif step == 3:
        st.header("📊 Step 2: Deal Snapshot")

        price = data["price"]
        rent = data["rent"]
        expenses = data["expenses"]
        down = data["down"]
        total_invest = price * down / 100
        annual_cf = (rent - expenses) * 12
        roi = (annual_cf / total_invest) * 100 if total_invest else 0
        cap = ((rent - expenses) * 12 / price) * 100 if price else 0
        score = min(roi, 20)/20*60 + min(cap, 10)/10*30 + (10 if annual_cf > 0 else -10)
        score = max(0, min(score, 100))

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("ROI", f"{roi:.1f}%")
        col2.metric("Cap Rate", f"{cap:.1f}%")
        col3.metric("Annual Cash Flow", f"${annual_cf:,.0f}")
        col4.metric("Score", f"{score:.1f}/100")

        st.markdown("✅ You’ve completed the quick walkthrough of our Quick Deal Analyzer!")
        st.markdown("Want to dive deeper?")

        if st.button("🚀 Go to Full Deal Analyzer"):
            st.session_state.page_redirect = "📊 Quick Deal Analyzer"
            st.rerun()


        if st.button("🔁 Start Over"):
            st.session_state.wizard_step = 1
            st.session_state.wizard_data = {}
            st.rerun()


    st.markdown("</div>", unsafe_allow_html=True)



# ─────────────────────────── QUICK DEAL ANALYZER ─────────────────────────────────────────────────────────────────────────────────────────────────────────────

elif page == "📊 Quick Deal Analyzer":
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.header("📊 Quick Deal Analyzer")
    st.markdown("Evaluate your deal with just a few inputs and see your score on a 0–100 scale.")

    with st.expander("📘 Key Terms"):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(tt("Cap Rate", "NOI ÷ Purchase Price"), unsafe_allow_html=True)
            st.markdown(tt("Monthly Cash Flow", "Rent - Expenses"), unsafe_allow_html=True)
        with col2:
            st.markdown(tt("ROI", "Annual Cash Flow ÷ Down Payment"), unsafe_allow_html=True)
            st.markdown(tt("Equity", "Value - Loan Balance"), unsafe_allow_html=True)

    st.markdown("### 🏷️ Property Details")
    prop_name = st.text_input("Property Name or Address", value="Untitled Deal")
    deal_type = st.selectbox("📂 Deal Type", ["Buy & Hold", "Fix & Flip", "BRRRR", "House Hack", "Wholesale", "Other"])
    notes = st.text_area("📝 Notes or Strategy", placeholder="Add notes, deal type, or plan (e.g., Fix & Flip, Buy & Hold, BRRRR)")
    tags = st.multiselect(
    "🏷️ Tags",
    options=["🔥 Hot Lead", "✅ Under Contract", "🧊 Cold Lead", "💼 Refi", "🛠 Rehab", "📦 Archived"],
    default=[]
    )
    col1, col2 = st.columns(2)
    with col1:
        price = st.number_input("Purchase Price ($)", min_value=-1e6, value=250000.0)
        rent = st.number_input("Monthly Rent ($)", min_value=-1e6, value=2200.0)
    with col2:
        expenses = st.number_input("Monthly Expenses ($)", min_value=-1e6, value=1400.0)
        down_pct = st.slider("Down Payment (%)", min_value=0.0, max_value=100.0, value=20.0, step=1.0)

    auto_tags = tags.copy() if tags else []

    if st.button("🔍 Analyze Deal"):
        st.session_state.analyzed = True
        st.session_state.price = price
        st.session_state.rent = rent
        st.session_state.expenses = expenses
        st.session_state.down_pct = down_pct

        annual_cf = (rent - expenses) * 12
        total_investment = price * down_pct / 100
        roi = (annual_cf / total_investment) * 100 if total_investment else 0
        cap_rate = ((rent - expenses) * 12 / price) * 100 if price else 0

        roi_score = min(roi, 20) / 20 * 60  
        cap_score = min(cap_rate, 10) / 10 * 30  
        cf_score = 10 if annual_cf > 0 else -10
        score = max(0, min(roi_score + cap_score + cf_score, 100))

        
        st.session_state.results = {
            "cf": annual_cf,
            "roi": roi,
            "cap": cap_rate,
            "score": score,
        }

        if score >= 85 and "🔥 Hot Lead" not in auto_tags:
            auto_tags.append("🔥 Hot Lead")
        elif score < 50 and "🧊 Cold Lead" not in auto_tags:
            auto_tags.append("🧊 Cold Lead")

        if roi >= 15 and "💼 Refi" not in auto_tags:
            auto_tags.append("💼 Refi")


        result = {
            "title": prop_name,
            "price": price,
            "rent": rent,
            "expenses": expenses,
            "roi": f"{roi:.1f}",
            "cap": f"{cap_rate:.1f}",
            "cf": annual_cf,
            "score": f"{score:.1f}",
            "type": deal_type,
            "tags": auto_tags, 
            "notes": notes,
            "status": "🔍 Reviewing"
            

        }

        if "deals" not in st.session_state:
            if os.path.exists("deals.json"):
                with open("deals.json", "r") as f:
                    st.session_state["deals"] = json.load(f)
            else:
                st.session_state["deals"] = []

        st.session_state["deals"].append(result)
        with open("deals.json", "w") as f:
            json.dump(st.session_state["deals"], f, indent=2)
        st.toast("💾 Deal saved to history.", icon="💾")


    if st.session_state.get("analyzed"):
        price = st.session_state.price
        rent = st.session_state.rent
        expenses = st.session_state.expenses
        down_pct = st.session_state.down_pct
        total_inv = price * down_pct / 100
        res = st.session_state.results

        st.markdown("### 📊 Deal Snapshot")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Annual Cash Flow", f"${res['cf']:,.0f}")
        c2.metric("ROI", f"{res['roi']:.1f}%")
        c3.metric("Cap Rate", f"{res['cap']:.1f}%")
        c4.metric("Score", f"{res['score']:.1f}/100")

        st.subheader("📊 Deal Score Breakdown")
        breakdown = {
            "Factor": ["ROI (max 20%)", "Cap Rate (max 10%)", "Cash Flow Sign"],
            "Value": [f"{res['roi']:.1f}%", f"{res['cap']:.1f}%", "Positive" if res['cf'] > 0 else "Negative"],
            "Weight": ["60%", "30%", "±10"],
            "Contribution": [f"{min(res['roi'], 20)/20*60:.1f}",
                             f"{min(res['cap'], 10)/10*30:.1f}",
                             f"{10 if res['cf'] > 0 else -10}"]
        }
        st.table(breakdown)



        st.subheader("💡 Suggestions to Improve Score")
        tips = []
        if res['roi'] < 10:
            tips.append("• Increase ROI: Try reducing your down payment or increasing rent.")
        if res['cap'] < 5:
            tips.append("• Improve Cap Rate: Lower expenses or negotiate a better purchase price.")
        if res['cf'] < 0:
            tips.append("• Cash flow is negative: Consider raising rent or cutting operating costs.")
        if res['score'] >= 85:
            summary = "✅ Great job! This deal scores very well under current assumptions."
        elif res['score'] >= 70:
            summary = "👍 Solid deal — there’s room to optimize further."
        elif res['score'] >= 50:
            summary = "⚠️ Fair deal — consider improving key metrics below."
        else:
            summary = "🚨 Risky deal — low score indicates poor returns or cash flow."
        st.markdown(summary)
        for t in tips:
            st.markdown(t)

        with st.expander("📘 Score Explanation"):
         st.markdown("""
**Deal Score Breakdown:**

- 🟢 **ROI (Return on Investment)** — Up to **60 points**  
  ROI is calculated as: `(Annual Cash Flow ÷ Down Payment) × 100`  
  - Max score: ROI of 20% = 60 points  
  - Example: 10% ROI = 30 points

- 🟡 **Cap Rate** — Up to **30 points**  
  Cap Rate is: `(Net Operating Income ÷ Purchase Price) × 100`  
  - Max score: Cap Rate of 10% = 30 points  
  - Example: 5% Cap = 15 points

- 🔵 **Cash Flow Sign** — ±10 points  
  - Positive = +10  
  - Negative = -10

---

**Total Score = ROI pts + Cap Rate pts + Cash Flow pts**

Score Range:
- 85–100: 🔥 Great deal
- 70–84: 👍 Solid
- 50–69: ⚠️ Needs improvement
- Below 50: 🚨 Risky or low return
    """)

        st.markdown("### 🧮 Quick Sensitivity Adjustment")
        rent_min, rent_max = int(rent * 0.8), int(rent * 1.2)
        exp_min, exp_max = int(expenses * 0.8), int(expenses * 1.2)
        col5, col6 = st.columns(2)
        with col5:
         adj_rent = st.slider("Adjusted Rent", rent_min, rent_max, value=(rent_min + rent_max) // 2, step=25, format="$%d")
        with col6:
         adj_exp = st.slider("Adjusted Expenses", exp_min, exp_max, value=(exp_min + exp_max) // 2, step=25, format="$%d")


        adj_cf = (adj_rent - adj_exp) * 12
        adj_roi = (adj_cf / total_inv) * 100 if total_inv else 0
        adj_cap = ((adj_rent - adj_exp) * 12 / price) * 100 if price else 0
        adj_score = min(adj_roi, 20)/20*60 + min(adj_cap, 10)/10*30 + (10 if adj_cf > 0 else -10)
        adj_score = max(0, min(adj_score, 100))

        d1, d2, d3, d4 = st.columns(4)
        d1.metric("Cash Flow", f"${adj_cf:,.0f}", f"{adj_cf - res['cf']:+,.0f}")
        d2.metric("ROI", f"{adj_roi:.1f}%", f"{adj_roi - res['roi']:+.1f}%")
        d3.metric("Cap Rate", f"{adj_cap:.1f}%", f"{adj_cap - res['cap']:+.1f}%")
        d4.metric("Score", f"{adj_score:.1f}", f"{adj_score - res['score']:+.1f}")

        st.subheader("📊 Monthly Expense Breakdown")

        
        with st.expander("⚙️ Adjust Assumptions"):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                ti_pct = st.number_input("Taxes & Insurance (% of Price)", 0.0, 10.0, 1.25, 0.1)
            with col2:
                maint_pct = st.number_input("Maintenance (% of Rent)", 0.0, 50.0, 10.0, 1.0)
            with col3:
                mgmt_pct = st.number_input("Management (% of Rent)", 0.0, 50.0, 8.0, 1.0)
            with col4:
                vac_pct = st.number_input("Vacancy Loss (% of Rent)", 0.0, 50.0, 5.0, 1.0)
                interest_rate_qda = st.number_input("Interest Rate (%)", 0.0, 20.0, 6.5)
                loan_term_qda = st.selectbox("Loan Term (Years)", [15, 20, 30], index=2)


        ti_month = price * (ti_pct / 100) / 12
        maint = rent * (maint_pct / 100)
        mgmt = rent * (mgmt_pct / 100)
        vacancy = rent * (vac_pct / 100)

        loan_amt = price * (1 - down_pct / 100)
        mort_rate = interest_rate_qda / 100 / 12
        months_qda = loan_term_qda * 12
        mortgage = loan_amt * mort_rate / (1 - (1 + mort_rate)**-months_qda) if loan_amt > 0 and mort_rate > 0 else 0

        total_exp = ti_month + maint + mgmt + vacancy + mortgage
        cash_flow = rent - expenses - total_exp

        labels = ["Mortgage (Est.)", "Taxes & Insurance", "Maintenance", "Management", "Vacancy Loss", "Cash Flow"]
        values = [mortgage, ti_month, maint, mgmt, vacancy, max(0, cash_flow)]

        pie_chart = go.Figure(data=[go.Pie(labels=labels, values=values, hole=0.4)])
        pie_chart.update_layout(
            title="Monthly Expense Breakdown",
            template="plotly_dark",
            margin=dict(l=30, r=30, t=40, b=30),
        )

        st.plotly_chart(pie_chart, use_container_width=True)

        
        st.markdown("### 🧾 Summary Table")
        exp_df = pd.DataFrame({
            "Category": labels,
            "Amount ($/mo)": [f"${v:,.0f}" for v in values]
        })
        st.dataframe(exp_df, use_container_width=True)
        csv_exp = export_csv_with_watermark(exp_df)
        st.download_button("⬇️ Download Expense Breakdown (CSV)", csv_exp, "monthly_expense_breakdown.csv", "text/csv")


# ───────────────────────────"👥 Tenant Affordability Tool"────────────────────────────────────────────────────────────────────────────────────────────────────────────

elif page == "👥 Tenant Affordability Tool":
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.header("👥 Tenant Affordability Tool")
    st.caption("Check if a rent amount is affordable based on income or vice versa.")

    st.markdown("### 🎯 Choose What to Calculate")
    mode = st.radio("Select Mode", ["Required Income from Rent", "Max Rent from Income"], horizontal=True)

    col1, col2 = st.columns(2)
    with col1:
        ratio = st.slider("Rent-to-Income Ratio (%)", 10, 50, 30, step=1)
    with col2:
        period = st.radio("Period Type", ["Monthly", "Annual"], horizontal=True)

    st.markdown("---")

    if mode == "Required Income from Rent":
        rent = st.number_input("Monthly Rent ($)", min_value=0.0, value=1800.0)
        monthly_income = rent / (ratio / 100)
        annual_income = monthly_income * 12

        st.success(f"✅ Required Monthly Income: **${monthly_income:,.0f}**")
        st.info(f"ℹ️ Annual Income Needed: **${annual_income:,.0f}**")

    elif mode == "Max Rent from Income":
        income = st.number_input(f"{period} Income ($)", min_value=0.0, value=60000.0)
        if period == "Monthly":
            max_rent = income * (ratio / 100)
        else:
            max_rent = (income / 12) * (ratio / 100)

        st.success(f"✅ Affordable Rent: **${max_rent:,.0f}/mo**")

    with st.expander("📘 What Is This?"):
        st.markdown("""
This tool helps you apply a common landlord rule:  
> **Rent should not exceed 30% of gross income**

- **Required Income from Rent**: How much a tenant should make to afford a given rent.
- **Max Rent from Income**: What rent a tenant can afford based on their income.

You can adjust the ratio for stricter or more lenient screening criteria.
        """)

    st.markdown("</div>", unsafe_allow_html=True)




# ─────────────────────────── BREAK-EVEN CALCULATOR ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
elif page == "💡 Break-Even Calculator":
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.header("💡 Break-Even Calculator")
    with st.expander("📘 Key Terms"):
        col1,col2 = st.columns(2)
        with col1:
            st.markdown(tt("Break-Even Rent","Minimum rent to cover mortgage + costs"), unsafe_allow_html=True)
            st.markdown(tt("Vacancy Rate","% of time property is empty"), unsafe_allow_html=True)
        with col2:
            st.markdown(tt("Maintenance %","% of rent reserved for repairs"), unsafe_allow_html=True)
            st.markdown(tt("Management %","% of rent paid to property manager"), unsafe_allow_html=True)

    c1,c2 = st.columns(2)
    with c1:
        price = st.number_input("Purchase Price ($)", min_value=-1e6, value=250000.0, step=1000.0)
        down_pct = st.slider("Down Payment (%)", min_value=0.0, max_value=100.0, value=20.0, step=1.0)
        int_rate = st.number_input("Loan Interest Rate (%)", min_value=0.0, value=6.5, step=0.1)

        term = st.selectbox("Loan Term (Years)",[15,30],index=1)
    with c2:
        ti = st.number_input("Taxes + Insurance + HOA ($/mo)", min_value=-1e6, value=300.0)
        maint_pct = st.slider("Maintenance (% of Rent)", min_value=0.0, max_value=50.0, value=10.0, step=1.0)
        mgmt_pct = st.slider("Management (% of Rent)", min_value=0.0, max_value=50.0, value=8.0, step=1.0)
        vac = st.slider("Vacancy Rate (%)", min_value=0.0, max_value=30.0, value=5.0, step=1.0)

    loan = price*(1-down_pct/100)
    m_int = int_rate/100/12
    months = term*12
    mortgage = npf.pmt(m_int,months,-loan) if loan>0 else 0

    def find_breakeven():
        for r in np.arange(500, 5000, 5):
            maint = r*maint_pct/100
            mgmt = r*mgmt_pct/100
            vac_loss = r*vac/100
            exp = ti+maint+mgmt+vac_loss
            cf = r-(mortgage+exp)
            if cf>=0:
                return r
        return None

    breakeven = find_breakeven()
    if breakeven:
        st.success(f"✅ Estimated Break-Even Rent: ${breakeven:,.0f}/mo")
        st.metric("Mortgage Payment",f"${mortgage:,.0f}/mo")
        rng = np.arange(breakeven-800,breakeven+800,50)
        cfs=[]
        for r in rng:
            m=r*maint_pct/100; mg=r*mgmt_pct/100; vl=r*vac/100; exp=ti+m+mg+vl; cfs.append(r-(mortgage+exp))
        fig = plot_line_chart("Cash Flow vs Rent", rng.tolist(), {"Cash Flow": cfs})
        st.plotly_chart(fig, use_container_width=True)
        df = pd.DataFrame({"Rent": rng, "Cash Flow": cfs})
        watermark = f"# Exported by RentIntel on {datetime.now().strftime('%Y-%m-%d')}\n"
        csv = (watermark + df.to_csv(index=False)).encode()
        st.download_button("⬇️ Download Cash Flow Table (CSV)",csv,"break_even_cash_flow.csv","text/csv")
    else:
        st.error("❌ No break-even rent found in range. Try adjusting inputs.")
    st.markdown("</div>", unsafe_allow_html=True)

# ─────────────────────────── Multi-Year ROI + Tax Insights ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
elif page == "📘 Multi-Year ROI + Tax Insights":
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.header("📘 Multi-Year ROI + Tax Insights")

    with st.expander("📘 Key Terms"):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(tt("Equity", "Property value minus loan balance"), unsafe_allow_html=True)
            st.markdown(tt("Rent Growth", "Annual rent increase (%)"), unsafe_allow_html=True)
            st.markdown(tt("Down Payment", "Initial cash invested"), unsafe_allow_html=True)
        with c2:
            st.markdown(tt("Expense Growth", "Annual expense increase (%)"), unsafe_allow_html=True)
            st.markdown(tt("Appreciation", "Annual property value growth (%)"), unsafe_allow_html=True)
            st.markdown(tt("Cash-on-Cash ROI", "Annual cash flow divided by cash invested (%)"), unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        price = st.number_input("Purchase Price ($)", 0.0, 1e9, 250000.0)
        dpct = st.slider("Down Payment (%)", 0.0, 100.0, 20.0, 1.0)
        rate = st.number_input("Interest Rate (%)", 0.0, 20.0, 6.5)
        term = st.selectbox("Loan Term (Years)", [15, 30], index=1)
        years = st.slider("Years to Project", 1, 30, 5)
    with c2:
        rent = st.number_input("Starting Monthly Rent ($)", 0.0, 1e5, 2200.0)
        exp = st.number_input("Monthly Expenses ($)", 0.0, 1e5, 800.0)
        rent_g = st.slider("Rent Growth (%/yr)", 0.0, 10.0, 3.0, 0.5)
        exp_g = st.slider("Expense Growth (%/yr)", 0.0, 10.0, 2.0, 0.5)
        appr = st.slider("Appreciation (%/yr)", 0.0, 10.0, 3.0, 0.5)

   
    st.markdown("---")
    st.subheader("🔧 Tax & Sale Inputs")
    land_pct = st.slider("Land Value Percentage (%)", 0, 50, 20, key="roi_land_pct")
    tax_rate = st.slider("Income Tax Rate (%)", 0, 50, 24, key="roi_tax_rate")
    sale_year = st.slider("Projected Sale Year", 1, years, years, key="roi_sale_year")

    dp = price * dpct / 100
    loan = price - dp
    mrate = rate / 100 / 12
    tot_months = term * 12
    mortgage = npf.pmt(mrate, tot_months, -loan)

    balance = loan
    value = price
    r = rent
    e = exp

    rows = []
    roi_cash_on_cash = []
    roi_equity_annualized = []
    roi_total_annualized = []
    after_tax_cf_list = []
    equity_list = []
    cash_flow_list = []

    for yr in range(1, years + 1):
        annual_cf = (r - e - mortgage) * 12

        
        for _ in range(12):
            interest = balance * mrate
            principal = mortgage - interest
            balance -= principal

        
        value *= (1 + appr / 100)

        
        equity = (value - balance) - dp

        
        building_value = price * (1 - land_pct / 100)
        annual_depr = building_value / 27.5

        
        tax_savings = annual_depr * tax_rate / 100

        
        after_tax_cf = annual_cf + tax_savings

        
        cash_on_cash = (annual_cf / dp) * 100 if dp != 0 else 0
        cash_on_cash_after_tax = (after_tax_cf / dp) * 100 if dp != 0 else 0
        equity_annualized = (equity / dp) * 100 / yr if dp != 0 else 0
        total_annualized = ((annual_cf + equity) / dp) * 100 / yr if dp != 0 else 0

        rows.append([
            yr,
            f"${r * 12:,.0f}",
            f"${e * 12:,.0f}",
            f"${annual_cf:,.0f}",
            f"${equity:,.0f}",
            f"${after_tax_cf:,.0f}",
            f"{cash_on_cash:.1f}%",
            f"{cash_on_cash_after_tax:.1f}%",
            f"{equity_annualized:.1f}%",
            f"{total_annualized:.1f}%"
        ])

        roi_cash_on_cash.append(cash_on_cash)
        roi_equity_annualized.append(equity_annualized)
        roi_total_annualized.append(total_annualized)
        after_tax_cf_list.append(after_tax_cf)
        equity_list.append(equity)
        cash_flow_list.append(annual_cf)

       
        r *= (1 + rent_g / 100)
        e *= (1 + exp_g / 100)

    df = pd.DataFrame(
        rows,
        columns=[
            "Year", "Annual Rent", "Annual Expenses", "Cash Flow", "Equity",
            "After-Tax Cash Flow", "Cash-on-Cash ROI", "After-Tax Cash-on-Cash ROI",
            "Equity ROI (Annualized)", "Total ROI (Annualized)"
        ]
    )

    with st.expander("📊 ROI Table & Chart", expanded=True):
        st.dataframe(df, use_container_width=True)
        st.plotly_chart(plot_line_chart("Projected ROI (%)", list(range(1, years + 1)), {
            "Cash-on-Cash ROI %": roi_cash_on_cash,
            "Equity ROI (Annualized) %": roi_equity_annualized,
            "Total ROI (Annualized) %": roi_total_annualized,
        }))
        csv = export_csv_with_watermark(df)
        st.download_button("⬇️ Download ROI Projection (CSV)", csv, "roi_projection.csv", "text/csv")

    with st.expander("📉 Depreciation & After-Tax Cash Flow"):
        st.markdown(f"**Building Value (Depreciable):** ${building_value:,.0f}")
        st.markdown(f"**Annual Depreciation:** ${annual_depr:,.0f}")
        st.markdown(f"**Estimated Tax Savings from Depreciation:** ${tax_savings:,.0f} (at {tax_rate}%)")
        st.markdown(f"**After-Tax Cash Flow Example (Year 1):** ${after_tax_cf_list[0]:,.0f}")

    with st.expander("📈 IRR Calculation"):

        initial_outflow = -dp
        cash_flows = [initial_outflow]
        
        for y in range(1, years + 1):
            if y == sale_year:

                prop_value_at_sale = price * ((1 + appr / 100) ** y)
                gain = prop_value_at_sale - price
                cap_gains_tax = gain * 0.15 
                selling_costs = prop_value_at_sale * 0.06
                net_sale_proceeds = equity_list[y-1] + dp - selling_costs - cap_gains_tax

                total_cash_flow = after_tax_cf_list[y-1] + net_sale_proceeds
                cash_flows.append(total_cash_flow)
            else:
                cash_flows.append(after_tax_cf_list[y-1])

        irr = npf.irr(cash_flows)
        irr_pct = irr * 100 if irr is not None else None

        st.markdown(f"**Internal Rate of Return (IRR) up to year {sale_year}:**")
        if irr_pct is not None and not pd.isna(irr_pct):
            st.metric(label="IRR (%)", value=f"{irr_pct:.2f}%")
        else:
            st.write("IRR could not be calculated with the provided inputs.")

    with st.expander("📊 Cash Flow vs Equity Growth Chart"):
        years_list = list(range(1, years + 1))
        st.plotly_chart(plot_dual_line_chart(
            "Annual Cash Flow vs Cumulative Equity",
            years_list,
            cash_flow_list,
            "Annual Cash Flow",
            equity_list,
            "Cumulative Equity Gain"
        ))

    st.markdown("</div>", unsafe_allow_html=True)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# 📘 Lending 101 Tab

elif page == "📑 Lender Package":
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.header("📁 Lender-Friendly Deal Package")

    tab1, tab2 = st.tabs(["📄 Summary", "ℹ️ How Lending Works"])

    deals = st.session_state.get("deals", [])
    if not deals:
        st.info("No deals found. Analyze a deal first.")
        st.stop()

    deal_titles = [d.get("title", "Untitled") for d in deals]
    selected = st.selectbox("Choose a Property", deal_titles)
    deal = next(d for d in deals if d.get("title", "Untitled") == selected)

    st.subheader("🏡 Property Overview")
    manual_address = st.text_input("Enter Property Address (if not saved)", value=deal.get('address', ''))
    st.write(f"**Title:** {deal.get('title', '-')}")
    st.write(f"**Address:** {deal.get('address', 'N/A')}")
    st.write(f"**Type:** {deal.get('type', '-')}")
    st.write(f"**Purchase Price:** ${deal.get('price', 0):,.0f}")
    down_pct = deal.get("down_pct", 20.0)
    st.write(f"**Down Payment:** {down_pct}%")
    loan_amount = deal.get("price", 0) * (1 - down_pct / 100)
    st.write(f"**Loan Amount:** ${loan_amount:,.0f}")

    st.subheader("💰 Financial Snapshot")
    st.metric("ROI", f"{deal.get('roi', 0)}%")
    st.metric("🏦 Cap Rate", f"{deal.get('cap', 0)}%")
    st.metric("Annual Cash Flow", f"${float(deal.get('cf', 0)):,.0f}")
    st.metric("Score", f"{deal.get('score', 0)}/100")

    st.subheader("👤 Borrower Information")
    borrower_name = st.text_input("Full Name", value="")
    borrower_email = st.text_input("Email", value="")
    income = st.number_input("Monthly Income ($)", value=6000)
    credit_score = st.slider("Credit Score", 300, 850, 700)
    dti_ratio = st.number_input("Other Monthly Debt Payments ($)", value=500)

    st.subheader("📋 Loan Qualification Snapshot")
    st.markdown("**Loan Criteria (Adjustable):**")
    custom_dscr = st.number_input("Min DSCR to Qualify", value=1.2)
    custom_dti = st.number_input("Max DTI % to Qualify", value=43.0)
    custom_ltv = st.number_input("Max LTV % to Qualify", value=80.0)
    loan_term = st.selectbox("Loan Term (Years)", [15, 20, 30], index=2)
    interest_rate = st.number_input("Interest Rate (%)", value=7.0, format="%.2f")
    prop_exp = float(deal.get("expenses", 0))
    rent_income = float(deal.get("rent", 0))

    monthly_rate = interest_rate / 100 / 12
    months = loan_term * 12
    est_mortgage = (loan_amount * monthly_rate) / (1 - (1 + monthly_rate) ** -months) if loan_amount > 0 and interest_rate > 0 else 0
    total_debt = est_mortgage + dti_ratio
    dti_percent = (total_debt / income) * 100 if income else 0
    dscr = rent_income / est_mortgage if est_mortgage else 0
    noi = rent_income - prop_exp
    ltv = (loan_amount / deal.get('price', 1)) * 100 if deal.get('price', 0) else 0
    qualifies_dscr = dscr >= custom_dscr
    qualifies_dti = dti_percent <= custom_dti
    qualifies_ltv = ltv <= custom_ltv

    col1, col2 = st.columns(2)
    col1.metric("Est. Monthly Mortgage (P&I)", f"${est_mortgage:,.0f}")
    col2.metric("DSCR", f"{dscr:.2f}" + (" ✅" if qualifies_dscr else " ❌"))
    st.metric("Debt-to-Income Ratio (DTI)", f"{dti_percent:.1f}%" + (" ✅" if qualifies_dti else " ❌"))
    st.metric("Net Operating Income (NOI)", f"${noi:,.0f}")
    st.metric("Loan-to-Value (LTV)", f"{ltv:.1f}%" + (" ✅" if qualifies_ltv else " ❌"))

    if qualifies_dscr and qualifies_dti and qualifies_ltv:
        st.success("✅ Likely to Qualify for Standard Investment Loan")
    else:
        st.error("⚠️ One or more loan requirements not met")

    fha_mode = st.checkbox("🏠 Evaluate for FHA Loan")
    fha_data = {}
    if fha_mode:
        fha_credit_ok = credit_score >= 580
        fha_dti_ok = dti_percent <= 57.0
        fha_ltv_ok = ltv <= 96.5
        fha_down_ok = down_pct >= 3.5

        mip_upfront = loan_amount * 0.0175
        mip_annual = loan_amount * 0.0055
        mip_monthly = mip_annual / 12
        total_monthly_payment = est_mortgage + mip_monthly
        st.metric("💰 Total Monthly Payment (Incl. MIP)", f"${total_monthly_payment:,.0f}")


        fha_data = {
            "FHA Evaluation Enabled": True,
            "FHA Credit Score OK": fha_credit_ok,
            "FHA DTI %": f"{dti_percent:.1f}%",
            "FHA LTV %": f"{ltv:.1f}%",
            "Down Payment %": f"{down_pct:.1f}%",
            "FHA Qualifies": fha_credit_ok and fha_dti_ok and fha_ltv_ok and fha_down_ok,
            "Upfront MIP": f"${mip_upfront:,.0f}",
            "Monthly MIP": f"${mip_monthly:,.0f}"
        }

        st.metric("FHA Credit Score OK", "✅" if fha_credit_ok else "❌")
        st.metric("FHA DTI ≤ 57%", fha_data["FHA DTI %"] + (" ✅" if fha_dti_ok else " ❌"))
        st.metric("FHA LTV ≤ 96.5%", fha_data["FHA LTV %"] + (" ✅" if fha_ltv_ok else " ❌"))
        st.metric("Down Payment ≥ 3.5%", fha_data["Down Payment %"] + (" ✅" if fha_down_ok else " ❌"))
        st.subheader("🏷️ Estimated FHA Mortgage Insurance")
        st.write(f"Upfront MIP: {fha_data['Upfront MIP']} (added to loan)")
        st.write(f"Monthly MIP Payment: {fha_data['Monthly MIP']}")

        if fha_data["FHA Qualifies"]:
            st.success("✅ Deal appears to qualify for FHA loan (assuming owner occupancy).")
        else:
            st.warning("⚠️ Deal does not currently meet all FHA loan requirements.")

    st.subheader("📈 Export Full Lender Package")
    if st.button("Export Lender PDF Package"):
        from fpdf import FPDF
        import os

        def sanitize_text(text):
            return str(text).encode("latin-1", "replace").decode("latin-1")

        def ensure_unicode_font(pdf, ttf_path="DejaVuSansCondensed.ttf"):
            if os.path.exists(ttf_path):
                try:
                    pdf.add_font('DejaVu', '', ttf_path, uni=True)
                    pdf.set_font('DejaVu', '', 12)
                    return ('DejaVu', True)
                except Exception:
                    pass
            pdf.set_font('Arial', '', 12)
            return ('Arial', False)

        pdf = FPDF()
        pdf.add_page()
        font_name, unicode_ok = ensure_unicode_font(pdf)

        title = sanitize_text(deal.get("title", "Untitled"))
        pdf.set_font(font_name, 'B', 16)
        pdf.cell(0, 10, f"Lender Deal Summary - {title}", ln=True)
        pdf.ln(2)

        pdf.set_font(font_name, '', 12)
        def row(label, value):
            pdf.cell(60, 8, f"{sanitize_text(label)}:", border=0)
            pdf.cell(0, 8, sanitize_text(value), ln=True)

        row("Borrower", borrower_name)
        row("Email", borrower_email)
        row("Property Address", manual_address)
        row("Type", deal.get("type", "-"))
        row("Purchase Price", f"${deal.get('price', 0):,.0f}")
        row("Monthly Rent", f"${deal.get('rent', 0):,.0f}")
        row("Monthly Expenses", f"${deal.get('expenses', 0):,.0f}")
        row("Loan Amount", f"${loan_amount:,.0f}")
        row("Loan Term", f"{loan_term} years")
        row("Interest Rate", f"{interest_rate:.2f}%")
        row("Est. Monthly Payment", f"${est_mortgage:,.0f}")
        row("Annual Cash Flow", f"${float(deal.get('cf', 0)):,.0f}")
        row("ROI", f"{float(deal.get('roi', 0)):.1f}%")
        row("Cap Rate", f"{float(deal.get('cap', 0)):.1f}%")
        row("Score", f"{float(deal.get('score', 0)):.1f}/100")

        pdf.ln(4)
        pdf.set_font(font_name, 'B', 13)
        pdf.cell(0, 8, sanitize_text("Borrower Qualification"), ln=True)
        pdf.set_font(font_name, '', 12)
        row("Monthly Income", f"${income:,.0f}")
        row("Other Debts", f"${dti_ratio:,.0f}")
        row("Credit Score", f"{credit_score}")
        row("Debt-to-Income Ratio", f"{dti_percent:.1f}%")
        row("DSCR", f"{dscr:.2f}")
        row("Loan Ready", "Yes" if qualifies_dscr and qualifies_dti and ltv <= 80 else "No")
        row("Net Operating Income (NOI)", f"${noi:,.0f}")
        row("Loan-to-Value (LTV)", f"{ltv:.1f}%")

        if fha_data.get("FHA Evaluation Enabled"):
            pdf.ln(4)
            pdf.set_font(font_name, 'B', 13)
            pdf.cell(0, 8, sanitize_text("FHA Loan Evaluation"), ln=True)
            pdf.set_font(font_name, '', 12)
            row("FHA Credit Score OK", "Yes" if fha_data["FHA Credit Score OK"] else "No")
            row("FHA DTI %", fha_data["FHA DTI %"])
            row("FHA LTV %", fha_data["FHA LTV %"])
            row("Down Payment %", fha_data["Down Payment %"])
            row("FHA Eligible", "Yes" if fha_data["FHA Qualifies"] else "No")
            row("Upfront MIP", fha_data["Upfront MIP"])
            row("Monthly MIP", fha_data["Monthly MIP"])

        notes = deal.get("notes", "")
        if notes:
            pdf.ln(4)
            pdf.set_font(font_name, 'B', 12)
            pdf.cell(0, 8, sanitize_text("Notes & Strategy"), ln=True)
            pdf.set_font(font_name, '', 11)
            pdf.multi_cell(0, 8, sanitize_text(notes))

        filename = "lender_package.pdf"
        pdf.output(filename)
        with open(filename, "rb") as f:
            st.download_button(
                label="Download Lender PDF",
                data=f.read(),
                file_name=filename,
                mime="application/pdf",
            )

    st.markdown("</div>", unsafe_allow_html=True)


    with tab2:
        st.subheader("ℹ️ What Do Lenders Look For?")
        st.markdown("""
        Understanding how lenders evaluate your investment property is critical for approval.

        ---
        ### 🧮 Key Metrics
        - **DSCR (Debt Service Coverage Ratio)** – Rent ÷ Mortgage. Most lenders want ≥ 1.2
        - **DTI (Debt-to-Income Ratio)** – Total monthly debts ÷ income. Target ≤ 43%
        - **LTV (Loan-to-Value)** – Loan ÷ Purchase Price. Target ≤ 80%

        ---
        ### 💡 Lender Expectations
        - Stable income and low personal debts
        - Credit score 620 or higher
        - Cash reserves (3–6 months recommended)
        - Positive cash flow or strong DSCR on the deal

        ---
        ### 🛠 Tips to Qualify
        - Increase rent or reduce expenses to boost DSCR
        - Lower your loan amount to improve LTV
        - Add a co-borrower or pay off debts to reduce DTI
        - Choose a longer loan term to lower your monthly payment

        This section helps you understand how small changes in your inputs can shift your ability to qualify.
        """)

    st.markdown("</div>", unsafe_allow_html=True)


#---------------------------📊 Portfolio Dashboard----------------------------------------------------
elif page == "📊 Portfolio Dashboard":
    import os
    from fpdf import FPDF

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.header("📊 Portfolio Dashboard")

    # ─────────────────────────── Helpers ───────────────────────────
    def safe_float(x, default=np.nan):
        if x is None:
            return default
        s = str(x).strip().replace(",", "")
        s = s.replace("%", "")
        try:
            return float(s)
        except:
            return default

    def build_portfolio_df(deals):
        rows = []
        for d in deals:
            rows.append({
                "Property": d.get("title", "-"),
                "Type": d.get("type", "-"),
                "Price": safe_float(d.get("price"), 0.0),
                "Rent": safe_float(d.get("rent"), 0.0),
                "Expenses": safe_float(d.get("expenses"), 0.0),
                "Cash Flow ($/yr)": safe_float(d.get("cf"), 0.0),
                "ROI (%)": safe_float(d.get("roi")),
                "Cap Rate (%)": safe_float(d.get("cap")),
                "Score": safe_float(d.get("score")),
                "Tags": d.get("tags", []),
                "Status": d.get("status", "—"),
            })
        df = pd.DataFrame(rows)
        if not df.empty:
            df["Cash Flow ($/mo)"] = df["Cash Flow ($/yr)"] / 12.0
            df["Tags (text)"] = df["Tags"].apply(lambda t: ", ".join(t) if isinstance(t, list) else str(t))
        return df

    def ensure_unicode_font(pdf: FPDF, preferred_ttf="DejaVuSansCondensed.ttf"):
        """
        Try to register and use a Unicode TTF font.
        If not found, fall back to core Arial (latin-1) but also degrade text a bit so it doesn't crash.
        Returns a tuple: (font_name_used, unicode_ok: bool)
        """
        if os.path.exists(preferred_ttf):
            try:
                pdf.add_font('DejaVu', '', preferred_ttf, uni=True)
                pdf.set_font('DejaVu', '', 12)
                return ('DejaVu', True)
            except Exception:
                pass
        
        pdf.set_font('Arial', '', 12)
        return ('Arial', False)

    def portfolio_pdf_unicode(df, filename="portfolio_summary.pdf"):
        """
        Unicode-capable PDF summary using a TTF font when available.
        If the font is missing, we’ll fall back to Arial and avoid bullets/emojis.
        """
        pdf = FPDF()
        pdf.add_page()
        font_name, unicode_ok = ensure_unicode_font(pdf)

        
        if unicode_ok:
            pdf.set_font(font_name, '', 16)
            pdf.set_font_size(16)
            pdf.cell(0, 10, "Portfolio Summary", ln=True)
        else:
            pdf.set_font('Arial', 'B', 16)
            pdf.cell(0, 10, "Portfolio Summary (Basic Font Mode)", ln=True)
        pdf.ln(2)

        
        pdf.set_font(font_name if unicode_ok else 'Arial', '', 12)
        total_cf = float(df["Cash Flow ($/yr)"].sum())
        avg_roi = df["ROI (%)"].mean(skipna=True)
        avg_cap = df["Cap Rate (%)"].mean(skipna=True)
        n_props = len(df)

        pdf.cell(0, 8, f"Properties: {n_props}", ln=True)
        pdf.cell(0, 8, f"Total Annual Cash Flow: ${total_cf:,.0f}", ln=True)
        if not np.isnan(avg_roi):
            pdf.cell(0, 8, f"Average ROI: {avg_roi:.1f}%", ln=True)
        if not np.isnan(avg_cap):
            pdf.cell(0, 8, f"Average Cap Rate: {avg_cap:.1f}%", ln=True)

        pdf.ln(4)
        if unicode_ok:
            pdf.set_font(font_name, '', 12)
            pdf.cell(0, 8, "Properties", ln=True)
            pdf.set_font(font_name, '', 11)
        else:
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 8, "Properties", ln=True)
            pdf.set_font('Arial', '', 11)

        
        for _, r in df.iterrows():
            title = r.get("Property", "-")
            
            if 'sanitize_text' in globals():
                title = sanitize_text(title)

            cf = float(r.get("Cash Flow ($/yr)", 0.0) or 0.0)
            roi = r.get("ROI (%)", np.nan)
            cap = r.get("Cap Rate (%)", np.nan)
            sc  = r.get("Score", np.nan)

           
            lead = "• " if unicode_ok else "- "
            pdf.cell(0, 7, f"{lead}{title}", ln=True)

            line = f"   CF: ${cf:,.0f}/yr"
            if not pd.isna(roi):
                line += f"  |  ROI: {float(roi):.1f}%"
            if not pd.isna(cap):
                line += f"  |  Cap: {float(cap):.1f}%"
            if not pd.isna(sc):
                line += f"  |  Score: {float(sc):.1f}"

            pdf.cell(0, 7, line, ln=True)

        pdf.output(filename)
        return filename

    # ─────────────────────────── Load deals ───────────────────────────
    deals = st.session_state.get("deals", [])
    if not deals:
        st.info("No deals saved yet. Add one in **📊 Quick Deal Analyzer**, then return here.")
        st.markdown("</div>", unsafe_allow_html=True)
        st.stop()

    df_all = build_portfolio_df(deals)

    # ─────────────────────────── Filters ───────────────────────────
    st.subheader("🔎 Filters")
    colf1, colf2, colf3 = st.columns([2, 2, 2])
    with colf1:
        all_types = sorted(list({d.get("type", "Other") for d in deals}))
        sel_types = st.multiselect("Deal Types", options=all_types, default=all_types)

    with colf2:
        all_tags = sorted(list({t for d in deals for t in d.get("tags", [])}))
        sel_tags = st.multiselect("Tags", options=all_tags, default=all_tags if all_tags else [])

    with colf3:
        name_query = st.text_input("Search by Property Name", value="").strip().lower()

    colr1, colr2, colr3 = st.columns(3)
    with colr1:
        roi_min, roi_max = st.slider("ROI Range (%)", -50.0, 100.0, (-50.0, 100.0))
    with colr2:
        cap_min, cap_max = st.slider("Cap Rate Range (%)", -10.0, 20.0, (-10.0, 20.0))
    with colr3:
        score_min = st.slider("Min Score", 0.0, 100.0, 0.0)

    df = df_all.copy()
    if sel_types:
        df = df[df["Type"].isin(sel_types)]
    if sel_tags:
        df = df[df["Tags"].apply(lambda tags: any(t in sel_tags for t in tags) if isinstance(tags, list) else False)]
    if name_query:
        df = df[df["Property"].str.lower().str.contains(name_query)]

    def in_range(x, lo, hi):
        if pd.isna(x):
            return False
        return (x >= lo) and (x <= hi)

    df = df[df["ROI (%)"].apply(lambda x: in_range(x, roi_min, roi_max))]
    df = df[df["Cap Rate (%)"].apply(lambda x: in_range(x, cap_min, cap_max))]
    df = df[df["Score"].fillna(0) >= score_min]

    if df.empty:
        st.warning("No properties match your filters.")
        st.markdown("</div>", unsafe_allow_html=True)
        st.stop()

    # ─────────────────────────── Summary bar ───────────────────────────
    total_cf = df["Cash Flow ($/yr)"].sum()
    avg_roi = df["ROI (%)"].mean(skipna=True)
    avg_cap = df["Cap Rate (%)"].mean(skipna=True)
    n_props = len(df)

    render_summary_bar(
        "🏘 Portfolio Overview",
        [
            ("# of Properties", f"{n_props}"),
            ("Total Annual Cash Flow", f"${total_cf:,.0f}"),
            ("Avg ROI", f"{avg_roi:.1f}%" if not np.isnan(avg_roi) else "—"),
            ("Avg Cap Rate", f"{avg_cap:.1f}%" if not np.isnan(avg_cap) else "—"),
        ],
    )

    # ─────────────────────────── Charts ───────────────────────────
    st.subheader("📈 Portfolio Charts")

    
    with st.expander("Cash Flow by Property (Annual)", expanded=True):
        bar = go.Figure()
        bar.add_trace(go.Bar(
            x=df["Property"],
            y=df["Cash Flow ($/yr)"],
            name="Annual Cash Flow",
        ))
        bar.update_layout(
            title="Annual Cash Flow by Property",
            plot_bgcolor="#18181b",
            paper_bgcolor="#18181b",
            font_color="#f3f3f3",
            xaxis=dict(gridcolor="#333"),
            yaxis=dict(gridcolor="#333"),
            margin=dict(l=30, r=30, t=40, b=30),
        )
        st.plotly_chart(bar, use_container_width=True)

    
    with st.expander("ROI vs Cap Rate (Bubble = Cash Flow)", expanded=True):
        scatter = go.Figure()
        sizes = np.interp(
            df["Cash Flow ($/yr)"].values,
            (df["Cash Flow ($/yr)"].min(), df["Cash Flow ($/yr)"].max()),
            (10, 40)
        ) if len(df) > 1 else [20] * len(df)
        scatter.add_trace(go.Scatter(
            x=df["ROI (%)"], y=df["Cap Rate (%)"],
            mode="markers+text",
            text=df["Property"],
            textposition="top center",
            marker=dict(size=sizes),
            name="Properties",
        ))
        scatter.update_layout(
            title="ROI vs Cap Rate",
            plot_bgcolor="#18181b",
            paper_bgcolor="#18181b",
            font_color="#f3f3f3",
            xaxis=dict(title="ROI (%)", gridcolor="#333"),
            yaxis=dict(title="Cap Rate (%)", gridcolor="#333"),
            margin=dict(l=30, r=30, t=40, b=30),
        )
        st.plotly_chart(scatter, use_container_width=True)

    
    with st.expander("Portfolio Composition (Cash Flow Share)", expanded=False):
        pie = go.Figure(data=[go.Pie(
            labels=df["Property"],
            values=df["Cash Flow ($/yr)"].clip(lower=0.0),  
            hole=0.4
        )])
        pie.update_layout(
            title="Share of Total Annual Cash Flow",
            template="plotly_dark",
            margin=dict(l=30, r=30, t=40, b=30),
        )
        st.plotly_chart(pie, use_container_width=True)

    # ─────────────────────────── Table + Sorting ───────────────────────────
    st.subheader("📋 Properties")
    sort_col = st.selectbox(
        "Sort by",
        ["Property", "ROI (%)", "Cap Rate (%)", "Cash Flow ($/yr)", "Score", "Type"],
        index=1
    )
    sort_dir = st.radio("Order", ["Descending", "Ascending"], horizontal=True, index=0)
    df_sorted = df.sort_values(by=sort_col, ascending=(sort_dir == "Ascending"), kind="mergesort")

    view_cols = ["Property", "Type", "Cash Flow ($/yr)", "Cash Flow ($/mo)", "ROI (%)", "Cap Rate (%)", "Score", "Status", "Tags (text)"]
    st.dataframe(df_sorted[view_cols], use_container_width=True)

    # ─────────────────────────── Exports ───────────────────────────
    st.subheader("⬇ Export")
    colx1, colx2 = st.columns(2)

    with colx1:
        csv_bytes = export_csv_with_watermark(df_sorted[view_cols])
        st.download_button("⬇ Download Portfolio CSV", csv_bytes, "portfolio_summary.csv", "text/csv")

    with colx2:
        
        filename = portfolio_pdf_unicode(df_sorted[["Property", "Cash Flow ($/yr)", "ROI (%)", "Cap Rate (%)", "Score"]].copy())
        with open(filename, "rb") as f:
            st.download_button(
                label="📄 Download Portfolio PDF",
                data=f.read(),
                file_name="portfolio_summary.pdf",
                mime="application/pdf",
            )

    st.markdown("</div>", unsafe_allow_html=True)


# ──────────────────────────── DEAL HISTORY ────────────────────────────

elif page == "📂 Deal History":
    import os, json, tempfile, re
    from fpdf import FPDF

    def latin1(txt):
        return str(txt).encode("latin-1", "replace").decode("latin-1")

    def generate_category_pdf(deals, category, filename):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 18)
        pdf.cell(0, 12, f"{category} Deal Summary", ln=True)
        pdf.set_font("Arial", '', 12)

        for deal in deals:
            pdf.ln(6)
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(0, 10, latin1(deal.get("title", "-")), ln=True)
            pdf.set_font("Arial", '', 11)

            def row(label, value):
                pdf.cell(50, 8, latin1(f"{label}:"), border=0)
                pdf.cell(0, 8, latin1(str(value)), ln=True)

            row("Type", deal.get("type", "-"))
            row("Purchase Price", f"${deal.get('price', 0):,}")
            row("Monthly Rent", f"${deal.get('rent', 0):,}")
            row("Monthly Expenses", f"${deal.get('expenses', 0):,}")
            row("Cash Flow", f"${float(deal.get('cf', 0)):,.0f}")
            row("ROI", f"{float(deal.get('roi', 0)):.1f}%")
            row("Cap Rate", f"{float(deal.get('cap', 0)):.1f}%")
            row("Score", f"{float(deal.get('score', 0)):.1f}/100")
            row("Status", deal.get("status", "—"))
            tag_colors = {
              "🔥 Hot Lead": "#f43f5e",
              "✅ Under Contract": "#22c55e",
              "🧊 Cold Lead": "#60a5fa",
              "💼 Refi": "#eab308",
              "🛠 Rehab": "#d97706",
              "📦 Archived": "#9ca3af"
             }
            tag_html = ""
            for tag in deal.get("tags", []):
                  color = tag_colors.get(tag, "#6b7280")
                  tag_html += f"<span style='background:{color};color:white;padding:2px 8px;border-radius:6px;margin-right:6px;font-size:12px;'>{tag}</span>"

            st.markdown(tag_html or "—", unsafe_allow_html=True)

            notes = deal.get("notes", "")
            if notes:
                pdf.multi_cell(0, 8, latin1(f"Notes: {notes}"))

            pdf.ln(4)

        pdf.output(filename)

    st.header("📂 Deal History")

    if "deals" not in st.session_state or not st.session_state["deals"]:
        st.info("No deals saved yet.")
        st.stop()

    all_tags = sorted({t for d in st.session_state["deals"] for t in d.get("tags", [])})
    all_statuses = sorted({d.get("status", "") for d in st.session_state["deals"]})
    vis_tags = st.multiselect("Filter by Tags", all_tags, default=all_tags or [])
    vis_statuses = st.multiselect("Filter by Status", all_statuses, default=all_statuses or [])

    visible_deals = [
        d for d in st.session_state["deals"]
        if (not vis_tags or set(d.get("tags", [])) & set(vis_tags))
        and (not vis_statuses or d.get("status", "") in vis_statuses)
    ]

    if not visible_deals:
        st.warning("No deals match the selected filters.")
        st.stop()

    deal_types = sorted({d.get("type", "Other") for d in visible_deals})
    for dtype in deal_types:
        st.subheader(f"📂 {dtype}")
        category_deals = [d for d in visible_deals if d.get("type") == dtype]

        for global_idx, deal in enumerate(category_deals):
            col1, col2 = st.columns([5, 1])
            with col1:
                st.markdown(f"**🏠 {deal['title']}**")
                st.caption(f"ROI: {deal.get('roi')}% | Cap Rate: {deal.get('cap')}% | CF: ${float(deal.get('cf', 0)):,.0f} | Score: {deal.get('score')}")

            with col2:
                if st.button("🗑 Delete", key=f"del_{dtype}_{global_idx}"):
                    st.session_state["deals"].remove(deal)
                    with open("deals.json", "w") as f:
                        json.dump(st.session_state["deals"], f, indent=2)
                    st.rerun()

       
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
            generate_category_pdf(category_deals, dtype, tmpfile.name)
            with open(tmpfile.name, "rb") as f:
                st.download_button(
                    label=f"📄 Export '{dtype}' Deals as PDF",
                    data=f.read(),
                    file_name=f"{dtype.replace(' ', '_')}_deals.pdf",
                    mime="application/pdf",
                    key=f"pdf_export_{dtype.replace(' ', '_')}"
                )

# ─────────────────Monte Carlo Sim ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

elif page == "📈 Monte Carlo Simulator":
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.header("📈 Monte Carlo ROI & IRR Simulation")

    tab1, tab2 = st.tabs(["📊 Simulator", "ℹ️ How It Works"])

    with tab2:
        st.subheader("ℹ️ What Is a Monte Carlo Simulation?")
        st.markdown("""
Monte Carlo simulation is a risk analysis technique that models uncertain outcomes by simulating many possible scenarios.

Instead of using fixed inputs (like "3% rent growth"), it randomly selects values within a range (e.g., 2%–5%) and runs hundreds or thousands of simulations.

This helps answer questions like:
- *What are the chances this deal earns more than 10% ROI?*
- *How much could ROI or IRR vary in a bad vs good market?*

---

### 📈 Chart Interpretation

**ROI Histogram**
- Shows the distribution of total return over the holding period.
- Example: If most ROI values are between 10%–15%, the investment is relatively stable.

**IRR Histogram**
- Shows the distribution of annualized returns across all simulations.
- IRR accounts for time and compounding, so it's a stronger measure for comparing investments.

---

### 🧠 Terms Defined

- **ROI (Return on Investment):**  
  (Total Profit ÷ Down Payment) × 100  
  Includes cash flow and equity from appreciation and loan paydown.

- **IRR (Internal Rate of Return):**  
  The annualized return over time, accounting for the timing of all cash flows (like yearly rent + resale proceeds).

---

This tool helps you **quantify uncertainty** and better understand how your assumptions impact outcomes.
        """)

    with tab1:
        st.markdown("Run randomized simulations to estimate how your investment might perform under uncertain market conditions.")
        st.markdown("*This is still a Work in progress*")

        
        col1, col2 = st.columns(2)
        with col1:
            price = st.number_input("Purchase Price ($)", min_value=-1e6, value=250000.0)
            down_pct = st.slider("Down Payment (%)", 0, 100, 20)
            loan = price * (1 - down_pct / 100)
            rate = st.number_input("Interest Rate (%)", min_value=-100.0, value=6.5)
            term = st.selectbox("Loan Term (Years)", [15, 30], index=1)
            start_rent = st.number_input("Starting Monthly Rent ($)", min_value=-1e6, value=2200.0)
        with col2:
            start_exp = st.number_input("Starting Monthly Expenses ($)", min_value=-1e6, value=800.0)
            years = st.slider("Years to Simulate", 1, 30, 5)
            num_simulations = st.slider("Number of Simulations", 100, 2000, 500, step=100)

            rent_range = st.slider("Rent Growth Range (%)", 0.0, 10.0, (0.0, 2.0))  # Narrowed range
            appr_range = st.slider("Appreciation Range (%)", 0.0, 10.0, (1.0, 2.0))  # Lower appreciation
            exp_range = st.slider("Expense Growth Range (%)", 0.0, 10.0, (3.0, 6.0))

           

        
        st.subheader("🔁 Running Simulations...")
        progress = st.progress(0)
        roi_results, irr_results = [], []
        cash_flows = []

        for i in range(num_simulations):
            r_growth = np.random.uniform(*rent_range)
            e_growth = np.random.uniform(*exp_range)
            v_growth = np.random.uniform(*appr_range)

            m_rate = rate / 100 / 12
            months = term * 12
            mortgage = npf.pmt(m_rate, months, -loan)

            r = start_rent
            e = start_exp
            val = price
            bal = loan
            cf_list = []
            cash_flows = [-price * down_pct / 100]

            for y in range(years):
             cf = (r - e - mortgage) * 12  
             cf_list.append(cf)
             cash_flows.append(cf)

             for _ in range(12):  
                 interest = bal * m_rate  
                 principal = mortgage - interest  
                 bal -= principal  

             val *= 1 + v_growth / 100 
             r *= 1 + r_growth / 100 
             e *= 1 + e_growth / 100

            sale_price = val
            sale_costs = 0.10 * sale_price
            net_proceeds = sale_price - sale_costs - bal
            roi = (sum(cf_list) + net_proceeds) / (price * down_pct / 100) * 100
            
            cash_flows[-1] += net_proceeds
            try:
                irr = npf.irr(cash_flows) * 100
            except:
                irr = 0
            roi_results.append(roi)
            irr_results.append(irr)
            
            progress.progress((i + 1) / num_simulations)

       
        st.subheader("📊 Summary Statistics")

        def summary_stats(name, data):
            arr = np.array(data)
            p10, med, p90 = np.percentile(arr, [10, 50, 90])
            st.markdown(f"**{name}**")
            st.write(f"• 10th Percentile: {p10:.1f}%")
            st.write(f"• Median: {med:.1f}%")
            st.write(f"• 90th Percentile: {p90:.1f}%")
            return arr

        roi_arr = summary_stats("ROI", roi_results)
        irr_arr = summary_stats("IRR", irr_results)

        
        st.subheader("📈 ROI Distribution")
        fig_roi = go.Figure()
        fig_roi.add_trace(go.Histogram(x=roi_arr, nbinsx=50, marker_color="#4ade80"))
        fig_roi.update_layout(title="ROI Distribution", plot_bgcolor="#18181b", paper_bgcolor="#18181b", font_color="#f3f3f3", margin=dict(l=30, r=30, t=40, b=30))
        st.plotly_chart(fig_roi, use_container_width=True)

        st.subheader("📈 IRR Distribution")
        fig_irr = go.Figure()
        fig_irr.add_trace(go.Histogram(x=irr_arr, nbinsx=50, marker_color="#38bdf8"))
        fig_irr.update_layout(title="IRR Distribution", plot_bgcolor="#18181b", paper_bgcolor="#18181b", font_color="#f3f3f3", margin=dict(l=30, r=30, t=40, b=30))
        st.plotly_chart(fig_irr, use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)


# ─────────────────────────── PROPERTY COMPARISON ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
elif page == "🏘 Property Comparison":
    import os
    from fpdf import FPDF

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.header("🏘 Property Comparison")

    # ──────────── Helpers ────────────
    def ensure_unicode_font(pdf: FPDF, ttf_path="DejaVuSansCondensed.ttf"):
        """Try to register a Unicode TTF font; fallback to Arial if missing."""
        if os.path.exists(ttf_path):
            try:
                pdf.add_font('DejaVu', '', ttf_path, uni=True)
                pdf.set_font('DejaVu', '', 12)
                return ('DejaVu', True)
            except:
                pass
        pdf.set_font('Arial', '', 12)
        return ('Arial', False)

    def comparison_to_pdf(df, filename="property_comparison.pdf"):
        """Export property comparison table to a PDF (Unicode‑safe)."""
        pdf = FPDF()
        pdf.add_page()
        font_name, unicode_ok = ensure_unicode_font(pdf)

        # Title
        pdf.set_font(font_name if unicode_ok else 'Arial', 'B', 16)
        pdf.cell(0, 10, "Property Comparison Report", ln=True)
        pdf.ln(5)

        pdf.set_font(font_name if unicode_ok else 'Arial', '', 10)
        bullet = "• " if unicode_ok else "- "
        keys = [
            "Purchase Price", "Monthly Rent", "Monthly Expenses",
            "Cash Flow", "Cap Rate", "ROI", "Score"
        ]

        for _, row in df.iterrows():
            prop_name = str(row.get("Property Name", "-"))
            if "sanitize_text" in globals():
                prop_name = sanitize_text(prop_name)

            # Property header row
            pdf.set_fill_color(240, 240, 240)
            pdf.set_font(font_name if unicode_ok else 'Arial', 'B', 11)
            pdf.cell(0, 8, f"{bullet}{prop_name}", ln=True, fill=True)

            # Metrics rows
            pdf.set_font(font_name if unicode_ok else 'Arial', '', 10)
            for key in keys:
                val = row.get(key, "-")
                # Format numbers nicely
                if isinstance(val, float):
                    if key in ["Cap Rate", "ROI"]:
                        val = f"{val:.1f}%"
                    elif key == "Score":
                        val = f"{val:.1f}"
                    else:
                        val = f"${val:,.2f}"
                elif isinstance(val, int):
                    if key in ["Purchase Price", "Monthly Rent", "Monthly Expenses", "Cash Flow"]:
                        val = f"${val:,}"
                pdf.cell(60, 8, f"{key}:", border=0)
                pdf.cell(0, 8, str(val), ln=True)
            pdf.ln(4)

        pdf.output(filename)
        return filename

    def export_csv(df):
        """CSV export with watermark."""
        watermark = f"# Exported by RentIntel on {datetime.now().strftime('%Y-%m-%d')}\n"
        return (watermark + df.to_csv(index=False)).encode()

    # ──────────── State ────────────
    if "comparison_inputs" not in st.session_state:
        st.session_state["comparison_inputs"] = []

    # ──────────── Quick Deal Snapshot Form ────────────
    with st.form("snapshot_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Property Name")
            price = st.number_input("Purchase Price ($)", min_value=0.0, step=1000.0)
            rent = st.number_input("Monthly Rent ($)", min_value=0.0, step=50.0)
            expenses = st.number_input("Monthly Expenses ($)", min_value=0.0, step=50.0)
        with col2:
            down_payment_pct = st.number_input("Down Payment (%)", min_value=0.0, max_value=100.0, value=20.0, step=1.0)
            interest_rate = st.number_input("Interest Rate (%)", min_value=0.0, max_value=20.0, value=6.5, step=0.1)
            loan_years = st.number_input("Loan Term (years)", min_value=1, max_value=40, value=30, step=1)

        submitted = st.form_submit_button("➕ Add Property (Auto‑Calculate)")

    if submitted:
        # Mortgage calculation (handles 0% rate)
        loan_amount = price * (1 - down_payment_pct / 100)
        monthly_rate = (interest_rate / 100) / 12
        n_payments = int(loan_years * 12)
        if loan_amount > 0 and n_payments > 0:
            if monthly_rate > 0:
                mortgage_payment = loan_amount * (monthly_rate * (1 + monthly_rate) ** n_payments) / ((1 + monthly_rate) ** n_payments - 1)
            else:
                mortgage_payment = loan_amount / n_payments
        else:
            mortgage_payment = 0.0

        # Auto‑calculated fields
        cash_flow = rent - expenses - mortgage_payment
        noi = (rent - expenses) * 12
        cap_rate = (noi / price) * 100 if price > 0 else 0.0
        annual_cash_flow = cash_flow * 12
        down_payment = price * (down_payment_pct / 100)
        roi = (annual_cash_flow / down_payment) * 100 if down_payment > 0 else 0.0

        # Deal Score (same spirit as your Quick Deal Analyzer weighting)
        # 60% ROI (cap at 20%), 30% Cap (cap at 10%), ±10 for CF sign
        roi_score = min(roi, 20) / 20 * 60
        cap_score = min(cap_rate, 10) / 10 * 30
        cf_score = 10 if cash_flow > 0 else -10
        score = max(0, min(roi_score + cap_score + cf_score, 100))

        st.session_state["comparison_inputs"].append({
            "Property Name": name or "Untitled Deal",
            "Purchase Price": float(price or 0),
            "Monthly Rent": float(rent or 0),
            "Monthly Expenses": float(expenses or 0),
            "Cash Flow": float(cash_flow),
            "Cap Rate": float(cap_rate),
            "ROI": float(roi),
            "Score": float(score),
        })
        st.success(f"Quick Deal Snapshot added: {name or 'Untitled Deal'}")

    # ──────────── Comparison Table & Row Actions ────────────
    if len(st.session_state["comparison_inputs"]) == 0:
        st.info("No properties added yet. Use the form above to add properties for comparison.")
    else:
        comparison_df = pd.DataFrame(st.session_state["comparison_inputs"])
        st.subheader("📋 Properties to Compare")
        st.dataframe(comparison_df, use_container_width=True)

        

        # Per‑row delete controls
        st.subheader("🗂 Manage Properties")
        for idx, prop in enumerate(list(st.session_state["comparison_inputs"])):
            c1, c2, c3, c4, c5 = st.columns([4, 2, 2, 2, 1])
            with c1:
                st.markdown(f"**{prop.get('Property Name','(no name)')}**")
            with c2:
                st.caption(f"ROI: {prop.get('ROI', 0):.1f}%")
            with c3:
                st.caption(f"Cap: {prop.get('Cap Rate', 0):.1f}%")
            with c4:
                st.caption(f"CF/mo: ${prop.get('Cash Flow', 0):,.0f}")
            with c5:
                if st.button("🗑", key=f"del_prop_{idx}", help="Delete this property"):
                    # Remove by index and rerun to refresh table/UI
                    st.session_state["comparison_inputs"].pop(idx)
                    st.rerun()

        st.markdown("---")
        # Clear all
        if st.button("🧹 Clear All Properties"):
            st.session_state["comparison_inputs"] = []
            st.rerun()

        # Exports
        col1, col2 = st.columns(2)
        with col1:
            csv_bytes = export_csv(comparison_df)
            st.download_button(
                "⬇ Export CSV",
                data=csv_bytes,
                file_name="property_comparison.csv",
                mime="text/csv"
            )
        with col2:
            pdf_filename = comparison_to_pdf(comparison_df)
            with open(pdf_filename, "rb") as f:
                st.download_button(
                    label="📄 Export PDF",
                    data=f.read(),
                    file_name="property_comparison.pdf",
                    mime="application/pdf"
                )

    st.markdown("</div>", unsafe_allow_html=True)

# ─────────────────────────── ADVANCED ANALYTICS ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
elif page == "🧪 Advanced Analytics":
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.header("🧪 Advanced Analytics & Forecasting (Pro)")

    scenario = st.radio("Scenario", ["Conservative", "Base", "Aggressive", "Custom"], horizontal=True)
    if scenario == "Conservative":
        rent_g, appr, exp_g = 1.5, 2.0, 3.0
    elif scenario == "Aggressive":
        rent_g, appr, exp_g = 4.0, 5.0, 1.5
    elif scenario == "Base":
        rent_g, appr, exp_g = 2.5, 3.0, 2.0
    else:
        rc1, rc2, rc3 = st.columns(3)
        with rc1: rent_g = st.number_input("Rent Growth %", min_value=0.0, value=2.5)
        with rc2: appr = st.number_input("Appreciation %", min_value=0.0, value=3.0)
        with rc3: exp_g = st.number_input("Expense Growth %", min_value=0.0, value=2.0)

    st.subheader("📋 Assumptions")
    c1, c2 = st.columns(2)
    with c1:
        price = st.number_input("Purchase Price ($)", min_value=0.0, value=250000.0)
        down_pct = st.slider("Down Payment %", 0, 100, 20)
        rate = st.number_input("Interest Rate (%)", min_value=0.0, value=6.5)
        term = st.selectbox("Loan Term (Years)", [15, 30], index=1)
    with c2:
        rent = st.number_input("Starting Monthly Rent ($)", min_value=0.0, value=2200.0)
        expenses = st.number_input("Starting Monthly Expenses ($)", min_value=0.0, value=800.0)
        exit_year = st.slider("Exit Year (Hold Period)", 1, 30, 5)

    down = price * down_pct / 100
    loan = price - down
    months = term * 12
    m_rate = rate / 100 / 12
    mortgage = npf.pmt(m_rate, months, -loan)

    balance = loan
    val = price
    r = rent
    e = expenses
    years = list(range(1, exit_year + 1))

    roi_list, equity_list, cf_list, table_rows = [], [], [], []
    cash_flows = [-down]  
    for y in years:
        
        cf = (r - e - mortgage) * 12

        principal_paid_year = 0
        
        for _ in range(12):
            interest = balance * m_rate
            principal = mortgage - interest
            balance -= principal
            principal_paid_year += principal

       
        val *= 1 + appr / 100

        
        equity = val - balance

       
        roi = ((cf + (equity - down)) / down) * 100 if down != 0 else 0

        roi_list.append(roi)
        equity_list.append(equity)
        cf_list.append(cf)
        table_rows.append([
            y,
            f"${r * 12:,.0f}",
            f"${e * 12:,.0f}",
            f"${cf:,.0f}",
            f"${equity:,.0f}",
            f"{roi:.1f}%"
        ])

        cash_flows.append(cf)

        
        r *= 1 + rent_g / 100
        e *= 1 + exp_g / 100

    
    sale_price = val
    selling_costs = 0.06 * sale_price
    net_sale_proceeds = sale_price - selling_costs - balance

    
    cash_flows[-1] += net_sale_proceeds  

    total_cash_flow = sum(cf_list)
    total_profit = net_sale_proceeds + total_cash_flow
    final_roi = (total_profit / down) * 100 if down != 0 else 0

    irr = npf.irr(cash_flows) * 100 if len(cash_flows) > 1 else 0

    st.subheader("📈 Exit Year Metrics")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Cash Flow", f"${total_cash_flow:,.0f}")
    col2.metric("Net Sale Proceeds", f"${net_sale_proceeds:,.0f}")
    col3.metric("Final ROI", f"{final_roi:.1f}%")
    col4.metric("Estimated IRR", f"{irr:.1f}%")

    st.subheader("📊 Year-by-Year Breakdown")
    df = pd.DataFrame(table_rows, columns=["Year", "Rent", "Expenses", "Cash Flow", "Equity", "ROI %"])
    st.dataframe(df, use_container_width=True)

    st.subheader("📉 Performance Chart")
    fig = plot_line_chart("Investment Projections", years, {
        "Annual Cash Flow": cf_list,
        "Equity": equity_list,
        "ROI %": roi_list
    })
    st.plotly_chart(fig, use_container_width=True)

    csv = df.copy()
    csv["IRR"] = f"{irr:.1f}%"
    csv_bytes = export_csv_with_watermark(csv)
    st.download_button("⬇️ Download Yearly ROI Table (CSV)", csv_bytes, "advanced_roi_projection.csv", "text/csv")

    st.markdown("</div>", unsafe_allow_html=True)



# ─────────────────────────── REHAB & REFI ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
elif page == "🏚 Rehab & Refi":
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.header("🏚 Renovation & Refinance Tools (Pro)")
    with st.expander("🛠️ Rehab ROI Calculator",expanded=True):
        r1,r2 = st.columns(2)
        with r1:
            price = st.number_input("Purchase Price ($)", min_value=-1e6, value=300000.0)
            dpct = st.slider("Down Payment %",0,100,20)
            dp = price*dpct/100
            rehab = st.number_input("Rehab Cost ($)", min_value=-1e6, value=25000.0, step=1000.0)
        with r2:
            loan_bal = st.number_input("Outstanding Loan Balance ($)", min_value=-1e6, value=240000.0)
            arv = st.number_input("After-Repair Value ($)", min_value=-1e6, value=275000.0, step=1000.0)
            months = st.slider("Months Until Rehab Complete",1,24,6)
        invested=dp+rehab; equity=arv-loan_bal; post_roi=((equity-invested)/invested)*100 if invested else 0
        st.metric("Total Invested",f"${invested:,.0f}"); st.metric("Equity After Rehab",f"${equity:,.0f}"); st.metric("Post-Rehab ROI",f"{post_roi:.1f}%")

    with st.expander("🔄 Refinance Explorer",expanded=False):
        c1,c2 = st.columns(2)
        with c1:
            refi_after = st.slider("Refinance After (Months)",1,360,12)
            new_rate = st.number_input("New Rate (%)", min_value=-100.0, value=5.0)
        with c2:
            new_term = st.selectbox("New Term (Years)",[15,20,30],2)
            cash_out = st.number_input("Cash-Out ($)", min_value=-1e6, value=0.0, step=1000.0)
        new_principal = loan_bal+cash_out; new_payment=npf.pmt(new_rate/100/12,new_term*12,-new_principal)
        st.metric("New Monthly Payment",f"${new_payment:,.2f}"); st.metric("New Loan Amount",f"${new_principal:,.0f}"); st.metric("Cash Pulled Out",f"${cash_out:,.0f}")
    st.markdown("</div>", unsafe_allow_html=True)


elif page == "📊 Deal Summary Comparison":
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.header("📊 Deal Summary Comparison")
    st.caption("Select multiple saved deals and compare their key metrics side-by-side.")

    if "deals" not in st.session_state or len(st.session_state["deals"]) < 2:
        st.info("You need at least two saved deals to compare.")
    else:
        deal_options = [f"{deal['title']} ({deal.get('type', '-')})" for deal in st.session_state["deals"]]
        selected_indices = st.multiselect(
            "Select Deals to Compare",
            options=list(range(len(deal_options))),
            format_func=lambda i: deal_options[i]
        )

        if len(selected_indices) >= 2:
            comparison_data = [st.session_state["deals"][i] for i in selected_indices]

           
            def score_emoji(score):
                score = float(score)
                if score >= 85:
                    return "🔥"
                elif score >= 70:
                    return "👍"
                elif score >= 50:
                    return "⚠️"
                else:
                    return "🚫"

            def roi_emoji(roi):
                roi = float(roi)
                return "💸" if roi >= 15 else "➕" if roi >= 8 else "⚠️"

            def cap_emoji(cap):
                cap = float(cap)
                return "🏦" if cap >= 6 else "➕" if cap >= 4 else "⚠️"

            def cf_emoji(cf):
                cf = float(cf)
                return "📈" if cf >= 400 else "➕" if cf >= 0 else "🔻"

            
            rows = [
                ("Title", [deal["title"] for deal in comparison_data]),
                ("Type", [deal.get("type", "") for deal in comparison_data]),
                ("ROI", [f"{float(deal['roi']):.1f}% {roi_emoji(deal['roi'])}" for deal in comparison_data]),
                ("Cap Rate", [f"{float(deal['cap']):.1f}% {cap_emoji(deal['cap'])}" for deal in comparison_data]),
                ("Cash Flow", [f"${float(deal['cf']):,.0f} {cf_emoji(deal['cf'])}" for deal in comparison_data]),
                ("Score", [f"{float(deal['score']):.1f} {score_emoji(deal['score'])}" for deal in comparison_data]),
            ]

            st.markdown("### 📋 Comparison Table with Emoji Indicators")
            for label, values in rows:
                cols = st.columns(len(values))
                for col, value in zip(cols, values):
                    col.metric(label if cols.index(col) == 0 else "", value)

    st.markdown("</div>", unsafe_allow_html=True)


#────────────────── Tax Benefits ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
elif page == "💸 Tax Benefits":
    import re, unicodedata

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.header("💸 Landlord Tax Benefits — Practical Guide")
    st.caption("Educational overview. Not tax advice. Verify with a licensed tax professional and current IRS publications.")

    # ---------- Helpers ----------
    def normalize_text_md(s: str) -> str:
        if not s:
            return s
        s = unicodedata.normalize("NFKC", s)
        s = re.sub(r"[\u200B-\u200D\uFEFF]", "", s)  # strip zero-width chars
        s = s.replace("∗", "*")
        return s

    def md(text: str):
        st.markdown(normalize_text_md(text), unsafe_allow_html=True)

    def callout(title: str, body: str):
        md(f"""
<div style="border-left:4px solid #4ade80; padding:10px 12px; background:#1f2937; border-radius:8px; margin:8px 0;">
  <div style="font-weight:600; margin-bottom:4px;">{title}</div>
  <div>{body}</div>
</div>
""")

    def irs_link(label: str, url: str) -> str:
        return f'<a href="{url}" target="_blank">{label}</a>'

    # ---------- IRS links (curated primary sources) ----------
    IRS = {
        "Pub527": ("Publication 527 — Residential Rental Property", "https://www.irs.gov/publications/p527"),
        "Pub925": ("Publication 925 — Passive Activity & At-Risk Rules", "https://www.irs.gov/publications/p925"),
        "Pub946": ("Publication 946 — Depreciation (MACRS)", "https://www.irs.gov/publications/p946"),
        "Form4562": ("Form 4562 — Depreciation & Amortization (Instructions)", "https://www.irs.gov/forms-pubs/about-form-4562"),
        "SchE": ("Schedule E — Supplemental Income (Instructions)", "https://www.irs.gov/forms-pubs/about-schedule-e-form-1040"),
        "Form8582": ("Form 8582 — Passive Activity Loss Limitations", "https://www.irs.gov/forms-pubs/about-form-8582"),
        "Pub535": ("Publication 535 — Business Expenses", "https://www.irs.gov/publications/p535"),
        "Pub463": ("Publication 463 — Travel, Gift, and Car Expenses", "https://www.irs.gov/publications/p463"),
        "Pub551": ("Publication 551 — Basis of Assets", "https://www.irs.gov/publications/p551"),
        "Pub544": ("Publication 544 — Sales & Other Dispositions of Assets", "https://www.irs.gov/publications/p544"),
        "Form8824": ("Form 8824 — Like-Kind Exchanges (Instructions)", "https://www.irs.gov/forms-pubs/about-form-8824"),
        "199A": ("Section 199A — Qualified Business Income (QBI) FAQ", "https://www.irs.gov/newsroom/qualified-business-income-deduction-section-199a"),
        "HomeOffice": ("Home Office (See Pub 587)", "https://www.irs.gov/publications/p587"),
        "PMI": ("Mortgage Insurance Premiums (See Instructions)", "https://www.irs.gov/credits-deductions/individuals/mortgage-insurance-premiums"),
    }

    # ---------- Topics data (Title, Body builder) ----------
    def sec_core_writeoffs():
        t = "Core Write‑Offs (Schedule E)"
        b = f"""
**What’s deductible annually** for rentals typically reported on Schedule E:
- **Mortgage interest** (on the rental loan)
- **Property taxes**, **insurance**, **HOA/condo fees**
- **Repairs & maintenance**, supplies, locks, small tools
- **Utilities** you pay (water, trash, gas/electric, internet if landlord-paid)
- **Professional fees** (management, legal, accounting, software)
- **Advertising & leasing costs**, tenant screening
- **Travel & vehicle** (property trips; see vehicle rules)
- **Depreciation** (building & certain improvements via MACRS)

{callout_html("What this means in plain English", "If you spent money **operating** the rental this year, it’s usually deductible **this year**, except long‑lived improvements—those are **depreciated** over time.")}

**Example.** Rent $2,200/mo; you pay $300 taxes/insurance, $80 HOA, $120 lawn, $50 repair supplies in March, $1,500 management for the year. All those are current deductions on **Schedule E**.

**Pro tips**
- Keep **separate bank/credit card** for rentals.
- Save **invoices/receipts**; export reports each year.
- If you **reimburse** a tenant for something that’s your expense, still deductible.

**Pitfalls**
- **Improvements ≠ repairs** — new roof or new HVAC is **not** a current expense; it’s depreciated.
- For mixed‑use (e.g., duplex + your unit), **allocate** expenses reasonably.

**IRS**: {link_line(["SchE","Pub527","Pub535"])}
"""
        return t, b

    def sec_depreciation():
        t = "Depreciation (27.5 years, MACRS)"
        b = f"""
You generally depreciate **residential building value** (not land) over **27.5 years** using **MACRS**. Most capital improvements (roof, HVAC, additions) are depreciated, too.

{callout_html("What this means in plain English", "When you buy a rental, you usually **cannot expense** the price in year 1. You **spread** the building’s cost over 27.5 years as an annual deduction. Land is not depreciable.")}

**Steps**
1. Determine **building vs. land** value (use county assessment or appraisal allocation).
2. Place in service date = available to rent.
3. Claim each year on **Form 4562** / **Schedule E**.

**Example.** Purchase $300,000; county shows land 20%. Building = $240,000. Annual depreciation ≈ $240,000 / 27.5 = **$8,727** (first/last year prorated).

**Pro tips**
- Keep **closing statement**; basis starts there (plus capitalized costs).
- Track improvements by date & cost; add to **depreciation schedule**.
- Consider **cost segregation** (engineered study) to reclassify some items into **5/7/15‑year** property (see a CPA).

**Pitfalls**
- **Land** is not depreciable.
- Depreciation taken (or **allowed**) reduces your **basis** and affects gain/recapture on sale.

**IRS**: {link_line(["Pub946","Form4562","Pub551","Pub527"])}
"""
        return t, b

    def sec_repairs_vs_improvements():
        t = "Repairs vs. Improvements"
        b = f"""
**Repairs** keep the property in operating condition (deduct now).  
**Improvements** **better** the property, **adapt** it to new use, or **restore** a major component (capitalize & depreciate).

{callout_html("What this means in plain English", "Fixing a leak or replacing a broken doorknob? **Repair**. Replacing the entire roof or adding a bedroom? **Improvement**.")}

**Safe harbors (talk to your CPA):**
- **De minimis** (often up to $2,500 per invoice/item with applicable policy) — expense small items.
- **Routine maintenance** — regular & expected upkeep can be expensed.
- **Small taxpayer safe harbor** — for certain buildings where total improvements fall under thresholds.

**Examples**
- Repair: patch drywall, fix a leak, replace a few shingles, small appliance part.
- Improvement: full roof, new HVAC, new kitchen cabinets, room addition.

**Pro tips**
- Keep **detailed descriptions** on invoices.
- Use safe harbors **consistently** and **document** policy.

**Pitfalls**
- Capitalizing when expensing is allowed (**missed deduction**).
- Expensing large restorations that should be capitalized (**audit risk**).

**IRS**: {link_line(["Pub535","Pub946","Pub527"])}
"""
        return t, b

    def sec_vehicle_travel():
        t = "Vehicle & Travel (Property Trips)"
        b = f"""
Trips for rental **management** are deductible:
- **Local travel**: standard mileage **or** actual expenses (choose one method).
- **Out‑of‑town** travel: transportation + lodging + incidental costs **if** primarily for rental business.

{callout_html("What this means in plain English", "Driving to meet a plumber, showing the unit, picking up supplies—those miles are deductible.")}

**Examples**
- Keep a **mileage log**: date, purpose, start/end miles.
- Out‑of‑town: keep **receipts**; track business purpose.

**Pro tips**
- Standard mileage rate (see current IRS rate) is **simple**; actual expenses require allocation & records.
- Parking/tolls are **add‑ons**.

**Pitfalls**
- **Commuting** miles are not deductible.
- Purely personal trips with a property stop **don’t qualify**.

**IRS**: {link_line(["Pub463","Pub535"])}
"""
        return t, b

    def sec_home_office():
        t = "Home Office (if your rental activity is a trade or business)"
        b = f"""
If your rental activity rises to a **trade or business**, a **home office** used **regularly and exclusively** for management can be deductible.

{callout_html("What this means in plain English", "If you truly run the rental like a business from a dedicated workspace at home, you may deduct a portion of home costs.")}

**Two methods**
- **Simplified**: set rate × sq ft (up to IRS limit)
- **Actual**: allocate mortgage interest/rent, utilities, insurance, etc.

**Pro tips**
- Document **exclusive** & **regular** use.
- If you only have one property & minimal activity, discuss **trade/business** status with a CPA.

**Pitfalls**
- Mixed personal use kills eligibility.
- Overstating business %.

**IRS**: {link_line(["HomeOffice","Pub535"])}
"""
        return t, b

    def sec_passive_losses():
        t = "$25,000 Passive Loss Allowance (Active Participation)"
        b = f"""
If you **actively participate** in your rental (approve tenants, set rents, OK repairs), you may deduct up to **$25,000** of **passive losses** against non‑passive income.  
This phases out **between $100,000 and $150,000** of **MAGI**; above **$150,000**, the allowance is **$0**.

{callout_html("What this means in plain English", "If your rentals show a tax loss, up to $25k of that loss may reduce your W‑2/other income—if you meet the participation and income rules.")}

**Pro tips**
- If losses are **suspended**, they carry forward and can offset future passive income or be freed on **disposition**.
- Keep **participation records** (emails, logs).

**Pitfalls**
- Confusing **active participation** (easier) with **material participation** (harder).
- Going over MAGI limits eliminates the allowance.

**IRS**: {link_line(["Pub925","Form8582","SchE"])}
"""
        return t, b

    def sec_real_estate_pro():
        t = "Real Estate Professional Status (REPS)"
        b = f"""
If you (and spouse filing jointly, combined) qualify as a **Real Estate Professional**, and **materially participate** in the rental activity, your rental losses may be **non‑passive** (can offset non‑passive income).

{callout_html("What this means in plain English", "If real estate is your day job and you’re deeply involved, your rental losses might offset W‑2 or business income.")}

**High‑level tests (see Pub 925/Regs)**
- **More than half** of personal services performed in real property trades or businesses; **and**
- **750+ hours** of services in those real property trades or businesses; **and**
- **Material participation** in the rental activity (or group activities with election).

**Pro tips**
- Keep **contemporaneous time logs**.
- Consider grouping elections; talk to a CPA.

**Pitfalls**
- Failing **material participation** even if you hit 750 hours in real estate **but not in the rentals**.
- Weak documentation.

**IRS**: {link_line(["Pub925"])}
"""
        return t, b

    def sec_qbi():
        t = "QBI (Section 199A) — 20% Deduction (Sometimes)"
        b = f"""
Some rental activities that qualify as a **trade or business** may get the **QBI deduction** (up to 20% of qualified income), subject to **thresholds, limitations, and complex rules**.

{callout_html("What this means in plain English", "If your rental counts as a business, you might get an extra deduction on the **profit**, not the gross rent.")}

**Pro tips**
- Safe harbor exists for certain rentals (recordkeeping, hours). Evaluate annually.
- QBI interacts with wages, capital, and income limits—**CPA recommended**.

**Pitfalls**
- Assuming **all** rentals qualify.
- Ignoring **phase‑outs** and wage/property tests at higher incomes.

**IRS**: {link_line(["199A","Pub535"])}
"""
        return t, b

    def sec_1031():
        t = "1031 Exchange (Like‑Kind) — Defer Gain"
        b = f"""
A **like‑kind exchange** lets you **defer** recognition of gain when exchanging investment real estate for other **like‑kind** real estate (strict timelines & rules apply).

{callout_html("What this means in plain English", "Sell one investment property and roll into another without paying tax **now**—but basis follows; you pay later when you sell unless you keep exchanging.")}

**Key ideas**
- Use a **qualified intermediary (QI)**.
- **45 days** to ID replacement; **180 days** to close.
- Exchange value & debt replacement matter.

**Pro tips**
- Coordinate with QI **before** closing the sale.
- Understand **basis carryover** and **depreciation recapture** effects.

**Pitfalls**
- Missing ID/closing deadlines.
- Touching the proceeds (disqualifies exchange).

**IRS**: {link_line(["Form8824","Pub544"])}
"""
        return t, b

    def sec_basis_closing():
        t = "Basis, Closing Costs & Adjustments"
        b = f"""
Your **basis** generally starts with purchase price plus certain **closing costs** (title, recording, some legal), plus **capital improvements**; reduced by depreciation and certain credits.

{callout_html("What this means in plain English", "Basis is your property’s “tax cost.” It’s crucial for depreciation now and gain later.")}

**Examples (generally added to basis)**
- Title fees, recording, certain legal fees, surveys
- Capital improvements after purchase

**Pro tips**
- Keep the **closing statement** and improvement logs.
- Separate **land vs. building** for depreciation.

**Pitfalls**
- Treating **loan costs** as basis (they’re usually amortized separately).
- Losing track of past depreciation (affects gain/recapture).

**IRS**: {link_line(["Pub551","Pub527"])}
"""
        return t, b

    def sec_loan_points_refi():
        t = "Loan Costs, Points & Refinance"
        b = f"""
**Loan origination costs** and **points** on a rental are generally **amortized** over the life of the loan (unlike a primary residence where points may be deductible that year).

{callout_html("What this means in plain English", "On rentals, most loan fees are not a one‑year deduction—you spread them across the loan term.")}

**Pro tips**
- Track amortization schedule (when you refi/payoff, remaining unamortized costs may be deductible).
- Separate **interest** (deduct annually) from **loan costs** (amortize).

**Pitfalls**
- Expensing all loan fees in one year.
- Forgetting to deduct remainder at **payoff/refi**.

**IRS**: {link_line(["Pub535","SchE"])}
"""
        return t, b

    def sec_sale_gain_recapture():
        t = "Selling a Rental: Gain, Depreciation Recapture"
        b = f"""
When you sell, total gain is affected by **accumulated depreciation** (recapture taxed up to 25%) and **capital gain** on the rest.

{callout_html("What this means in plain English", "You got deductions for depreciation; when you sell, the IRS may tax that part differently (**recapture**), and the rest at capital‑gains rates.")}

**Pro tips**
- Keep a **depreciation ledger** (years of deductions).
- Closing costs at sale may **reduce** amount realized.

**Pitfalls**
- Forgetting recapture.
- Misstating basis (esp. missed/allowed depreciation).

**IRS**: {link_line(["Pub544","Pub551","SchE"])}
"""
        return t, b

    # helpers to format callout and link list
    def callout_html(title, body):
        return f"""
<div style="border-left:4px solid #4ade80; padding:10px 12px; background:#111827; border-radius:8px; margin:8px 0;">
  <div style="font-weight:600; margin-bottom:4px;">{title}</div>
  <div>{body}</div>
</div>
"""

    def link_line(keys):
        links = [irs_link(IRS[k][0], IRS[k][1]) for k in keys if k in IRS]
        return " • ".join(links)

    # Build the master list of sections
    SECTIONS = [
        sec_core_writeoffs(),
        sec_depreciation(),
        sec_repairs_vs_improvements(),
        sec_vehicle_travel(),
        sec_home_office(),
        sec_passive_losses(),
        sec_real_estate_pro(),
        sec_qbi(),
        sec_1031(),
        sec_basis_closing(),
        sec_loan_points_refi(),
        sec_sale_gain_recapture(),
    ]

    # ---------- Filters / Search ----------
    st.subheader("Find What You Need Fast")
    left, right = st.columns([2, 1])
    with left:
        query = st.text_input("Search topics or keywords (e.g., “depreciation”, “vehicle”, “QBI”, “loss”):", "").strip().lower()
    with right:
        # allow quick topic selection
        titles = [t for t, _ in SECTIONS]
        selected = st.multiselect("Show only these topics (optional):", titles, default=[])

    def matches(title, body, q):
        if not q:
            return True
        hay = (title + " " + body).lower()
        return all(word in hay for word in q.split())

    # ---------- Render ----------
    shown = 0
    for title, body in SECTIONS:
        if selected and title not in selected:
            continue
        if not matches(title, body, query):
            continue
        with st.expander(f"📌 {title}", expanded=False):
            md(body)
        shown += 1

    if shown == 0:
        st.info("No sections match your search. Try different keywords or clear filters.")

    md("""
<hr style="border: none; border-top: 1px solid #333; margin: 16px 0;" />
<small><strong>Disclaimer:</strong> This page is an educational summary. Tax rules change and have exceptions. Confirm with a qualified tax professional and the latest IRS publications.</small>
""")

    st.markdown("</div>", unsafe_allow_html=True)
# ─────────────────────────── GLOSSARY ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
elif page == "📖 Help & Info":
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.header("📖 Real Estate Glossary & Methodology")
    st.markdown("*A beginner-friendly guide to key real estate terms and how our estimates work.*")

    search_term = st.text_input("🔎 Search for a term (e.g. 'cap rate', 'loan')").strip().lower()

    # Helper to filter a block by search term
    def show_if_match(title: str, terms: list[str]):
        if not search_term:
            return True
        combined = title.lower() + " " + " ".join(terms).lower()
        return search_term in combined
    # ─────────────────────────────────────────────────────────────────────────────
    # 💰 Cash Flow & Returns
    # ─────────────────────────────────────────────────────────────────────────────
    with st.expander("💰 Cash Flow & Returns"):
        st.markdown("""
- **Cash Flow** 📈: Money left over each month after paying all expenses and debt service.
- **Cash Flow (Annual)** 📅: Monthly cash flow × 12.
- **ROI (Return on Investment)** 💸: Annual profit ÷ initial cash invested.
- **Cash‑on‑Cash Return** 💵: (Annual pre‑tax cash flow ÷ cash invested) × 100.
- **Cap Rate** 🏦: NOI ÷ Purchase Price (ignores financing).
- **NOI (Net Operating Income)** 🧮: Rent + other income − operating expenses (excludes mortgage & CapEx).
- **IRR (Internal Rate of Return)** ⏳: Annualized return accounting for timing of cash flows.
- **MIRR** 🔁: IRR variant using explicit reinvest/finance rates.
- **NPV (Net Present Value)** 🧾: Present value of cash flows minus initial investment.
- **Equity** 💎: Property value − loan balance.
- **Appreciation** 📈: Value increase over time (market or forced via rehab).
- **Total Return** 🧾: Cash flow + principal paydown + appreciation (± taxes).
- **Breakeven Occupancy** ⚖️: Occupancy % needed so NOI covers debt service & fixed costs.
- **Operating Expense Ratio (OER)** 📊: OpEx ÷ Effective Gross Income.
- **Expense Ratio to Rent** 🧯: Operating expenses ÷ gross rent.
- **1% Rule** 🔍: Target monthly rent ≈ 1% of price (quick screen; not definitive).
- **50% Rule** ⛑️: Assume ~50% of rent goes to OpEx before mortgage (rule of thumb).
- **70% Rule (Flips)** 🔨: Max offer ≈ 70% × ARV − repairs.
- **Payback Period** ⏱️: Time to recover initial cash investment from cash flow.
        """)

    # ─────────────────────────────────────────────────────────────────────────────
    # 🏠 Property Terms
    # ─────────────────────────────────────────────────────────────────────────────
    with st.expander("🏠 Property Terms"):
        st.markdown("""
- **Purchase Price** 💲: Contract price to acquire the property.
- **After‑Repair Value (ARV)** 🛠️: Estimated value after renovations.
- **Comps / CMA** 🏘️: Comparable sales/market analysis to gauge value.
- **T12 / Trailing 12** 📆: Last 12 months of actual income/expenses.
- **Pro Forma** 📄: Forward‑looking income/expense projection.
- **Rent Roll** 🧾: Unit‑level rent & lease snapshot.
- **Sq Ft (Square Footage)** 📏: Size used for pricing/rents.
- **Gross Building Area (GBA)** 🧱: Total building area; **Net Rentable** excludes common areas.
- **Beds/Baths** 🛌🛁: Unit mix details affecting rent.
- **Zoning** 🧭: Permitted uses; may restrict STRs, ADUs, density.
- **Easement** 🛤️: Right for others to use part of the property (utilities/access).
- **Encumbrance/Lien** 🧷: Claim on the property (e.g., mortgage, tax lien).
- **HOA/COA** 🏘️: Association fees & rules for communities/condos.
- **Utility Setup** 💡: Landlord/tenant responsibility (RUBS, sub‑metering).
- **ADU** 🧩: Accessory dwelling unit (extra rentable space).
        """)

    # ─────────────────────────────────────────────────────────────────────────────
    # 📊 Deal Analysis Metrics
    # ─────────────────────────────────────────────────────────────────────────────
    with st.expander("📊 Deal Analysis Metrics"):
        st.markdown("""
- **Gross Scheduled Rent (GSR)** 🗓️: Rent at 100% occupancy before losses.
- **Vacancy Loss** 🚪: GSR × vacancy rate.
- **Loss to Lease (LTL)** 📉: Difference between market rent and actual rent.
- **Other Income** ➕: Laundry, parking, pet fees, RUBS, etc.
- **Effective Gross Income (EGI)** ✅: GSR − vacancy + other income.
- **Operating Expenses (OpEx)** 🧯: Taxes, insurance, repairs, mgmt, utilities (ex‑CapEx).
- **Capital Expenditures (CapEx)** 🧱: Big‑ticket replacements (roof, HVAC, parking).
- **Replacement Reserve** 🧰: Annual set‑aside for future CapEx.
- **GRM (Gross Rent Multiplier)** 📐: Price ÷ Annual Gross Rent.
- **DSCR (Debt Service Coverage Ratio)** 🛡️: NOI ÷ Annual debt service (≥1.20 preferred).
- **DTI (Debt‑to‑Income)** 📉: Borrower debt payments ÷ income.
- **LTV (Loan‑to‑Value)** ⚖️: Loan ÷ value; **LTC**: Loan ÷ total project cost.
- **OCC (Occupancy)** 🛏️/**Vacancy** 🚪: % occupied vs. vacant units.
- **Breakeven Rent** 💡: Rent needed monthly to reach $0 cash flow.
- **Sensitivity / Scenario** 🔁: Vary key inputs to see outcome ranges.
        """)

    # ─────────────────────────────────────────────────────────────────────────────
    # 📈 Valuation & Underwriting
    # ─────────────────────────────────────────────────────────────────────────────
    with st.expander("📈 Valuation & Underwriting"):
        st.markdown("""
- **Income Approach** 💼: Value from NOI and cap rate (Value = NOI / Cap).
- **Sales Comparison** 🏷️: Value from similar recent sales (cap, $/unit, $/sqft).
- **Cost Approach** 🧮: Land value + replacement cost − depreciation.
- **BOV / BPO** 🧑‍💼: Broker Opinion of Value / Price Opinion.
- **Cap Rate Reversion** 🔁: Exit cap assumption at sale.
- **Discount Rate** 📉: Required rate to discount future cash flows (DCF).
- **Going‑In vs. Stabilized** ⚙️: Current metrics vs. post‑improvements/lease‑up.
- **Stress Test** 🧪: Shock interest rates, rents, expenses to assess risk.
- **Margin of Safety** 🧩: Cushion between projections and breakeven thresholds.
        """)

    # ─────────────────────────────────────────────────────────────────────────────
    # 📉 Financing & Mortgages
    # ─────────────────────────────────────────────────────────────────────────────
    with st.expander("📉 Financing & Mortgages"):
        st.markdown("""
- **Down Payment** 💳: Cash invested at purchase (e.g., 20%).
- **Interest Rate** 📈: Cost of borrowing; fixed vs. adjustable (ARM).
- **Amortization** ⏱️: How principal is paid down over time.
- **Points / Origination** 🎯: Up‑front % fees for the lender/broker.
- **PMI/MIP** 🛡️: Mortgage insurance (conventional/FHA) when low down payment.
- **Prepayment Penalty** 🚫: Fee for paying off loan early (common in commercial).
- **IO (Interest‑Only)** 💤: Period with no principal paydown.
- **Balloon** 🎈: Large payoff due at maturity.
- **Bridge Loan** 🌉: Short‑term financing until permanent loan/refi.
- **Blanket / Portfolio Loan** 🧺: One loan for multiple properties; lender holds in‑house.
- **Non‑Recourse vs Recourse** ⚖️: Borrower’s personal liability limited or not.
- **Rate Buydown / 2‑1 Buydown** ⬇️: Up‑front payment to temporarily/lower rate.
- **Seasoning** 🗓️: Time a loan or rent history must exist for underwriting.
        """)

    # ─────────────────────────────────────────────────────────────────────────────
    # 🧾 Taxes & Write‑Offs
    # ─────────────────────────────────────────────────────────────────────────────
    with st.expander("🧾 Taxes & Write-Offs"):
        st.markdown("""
- **Depreciation** 📉: Residential 27.5‑year straight‑line (building only).
- **Depreciation Recapture** 🔄: Tax on prior depreciation when selling.
- **Adjusted Basis** 🧮: Purchase price ± improvements − depreciation.
- **Capital Gains** 🧾: Profit on sale; short‑ vs long‑term.
- **1031 Exchange** 🔁: Defer gains by exchanging into a like‑kind property.
- **721/UPREIT** 🏢: Contribute property to an operating partnership for OP units.
- **Cost Segregation** 🧠: Accelerate depreciation by reclassifying components.
- **Bonus Depreciation** ⚡: Additional first‑year depreciation (subject to current law).
- **Passive Activity Rules** 💤: Limits on offsetting active income with rental losses.
- **QBI (199A)** 💼: Potential 20% deduction on qualified business income (rules apply).
- **Schedule E** 📄: IRS form for rental income/expenses.
- **Audit Trail** 📚: Receipts & records supporting deductions.
        """)

    # ─────────────────────────────────────────────────────────────────────────────
    # 🧰 Operating Expenses & Management
    # ─────────────────────────────────────────────────────────────────────────────
    with st.expander("🧰 Operating Expenses & Management"):
        st.markdown("""
- **Repairs vs. Improvements** 🛠️: Repairs are expensed; improvements are capitalized/depreciated.
- **Turnover / Make‑Ready** 🔁: Preparing a unit between tenants.
- **Property Management Fee** 👷: % of collected rent (or flat).
- **Leasing Fee** 📝: One‑time fee for new tenancy.
- **RUBS** 💧: Ratio utility billing to tenants (water/sewer/trash).
- **Common Utilities** 🔌: Landlord‑paid electric/gas/water for common areas.
- **Insurance Premiums** 🛡️: Hazard, liability, flood, umbrella.
- **Reserves** 💼: Monthly/annual set‑asides for CapEx and contingencies.
- **Bad Debt / Concessions** 🚫: Uncollectible rent or discounts.
        """)

    # ─────────────────────────────────────────────────────────────────────────────
    # 🧠 Strategy Terms
    # ─────────────────────────────────────────────────────────────────────────────
    with st.expander("🧠 Strategy Terms"):
        st.markdown("""
- **BRRRR** 🔁: Buy, Rehab, Rent, Refinance, Repeat.
- **Buy & Hold** 🏠: Long‑term rentals for cash flow + appreciation.
- **Fix & Flip** 🔨: Renovate and resell quickly for profit.
- **House Hacking** 🧍🏠: Live in part, rent the rest.
- **Wholesale** 📦: Assign a purchase contract for a fee.
- **Value‑Add** 🧩: Improvements/ops tweaks that increase NOI and value.
- **Syndication** 🤝: Group investment; GP/LP structure.
- **Preferred Return (“Pref”)** ⭐: LPs get a baseline return before GP promote.
- **Waterfall / Promote** 💧: Profit split tiers after hurdles.
        """)

    # ─────────────────────────────────────────────────────────────────────────────
    # 🏗️ Property Types & Use Cases
    # ─────────────────────────────────────────────────────────────────────────────
    with st.expander("🏗️ Property Types & Use Cases"):
        st.markdown("""
- **SFR / SFH** 🏡: Single‑family rental/home.
- **Duplex/Triplex/Quad** 🧱: 2‑4 units (residential lending).
- **Small Multifamily** 🏢: 5–50 units (commercial lending).
- **Large Multifamily** 🏙️: 50+ units; institutional style.
- **MTR / STR** 🛏️: Mid‑term (30–90 days) / Short‑term (<30 days) rentals.
- **Student / Workforce / Section 8** 🎓💼🏷️: Niche strategies with unique rules.
- **Mixed‑Use** 🧩: Combine residential + retail/office.
        """)

    # ─────────────────────────────────────────────────────────────────────────────
    # 📜 Legal & Structures
    # ─────────────────────────────────────────────────────────────────────────────
    with st.expander("📜 Legal & Deal Structures"):
        st.markdown("""
- **LLC / LP / GP** 🧾: Common ownership/management structures.
- **Operating Agreement** 🤝: Governs roles, splits, decisions.
- **JV (Joint Venture)** 🤝: Two+ parties partner on a deal.
- **PPM (Private Placement Memorandum)** 📑: Disclosure in syndications.
- **Accredited Investor** 💼: Meets income/net‑worth criteria.
- **506(b) / 506(c)** 🏛️: Securities exemptions (regarding solicitation/verification).
- **Title Insurance** 🪪: Protects against title defects.
- **Deed** 📜: Transfers ownership; warranty vs. quitclaim.
- **Escrow / Earnest Money** 💰: Neutral funds holder / good‑faith deposit.
        """)

    # ─────────────────────────────────────────────────────────────────────────────
    # 📄 Documents & Due Diligence
    # ─────────────────────────────────────────────────────────────────────────────
    with st.expander("📄 Documents & Due Diligence"):
        st.markdown("""
- **PSA (Purchase & Sale Agreement)** ✍️: Contract to buy/sell.
- **Addenda / Contingencies** 🧷: Inspection, financing, appraisal outs.
- **Inspection** 🔎: Property condition review; sewer scope, roof, foundation.
- **Appraisal** 🧮: Lender’s value opinion for underwriting.
- **Survey / ALTA** 🗺️: Boundaries, easements, encroachments.
- **Phase I ESA** 🧪: Environmental site assessment (commercial).
- **Operating Memorandum / OM** 📊: Offering details and pro forma.
- **W‑9, Rent Ledgers, Leases** 🧾: Verify income/tenancies.
- **Estoppels** 📝: Tenant confirms lease terms & balances.
        """)

    # ─────────────────────────────────────────────────────────────────────────────
    # 🛏️ Short‑ & Mid‑Term Rentals (STR/MTR)
    # ─────────────────────────────────────────────────────────────────────────────
    with st.expander("🛏️ Short‑ & Mid‑Term Rentals (STR/MTR)"):
        st.markdown("""
- **ADR (Avg Daily Rate)** 📅: Average nightly rate.
- **RevPAR** 💵: Revenue per available room/night.
- **Occupancy (STR)** 🛌: Booked nights ÷ available nights.
- **Cleaning/Turnover** 🧼: Between‑stay service and supplies.
- **Channel Fees** 🌐: OTA platform fees (e.g., Airbnb/VRBO).
- **Local Ordinances** 🏛️: STR permits, caps, and taxes.
        """)

    # ─────────────────────────────────────────────────────────────────────────────
    # 🏬 Commercial & Lease Types
    # ─────────────────────────────────────────────────────────────────────────────
    with st.expander("🏬 Commercial & Lease Types"):
        st.markdown("""
- **NNN (Triple Net)** 🧾: Tenant pays taxes, insurance, maintenance.
- **Gross / Full‑Service** 🧾: Landlord pays most operating costs.
- **Modified Gross** 🧾: Cost sharing varies by lease.
- **TI (Tenant Improvements)** 🔧: Landlord build‑out allowance.
- **CAM (Common Area Maintenance)** 🧯: Shared area expenses rebilled to tenants.
- **Percentage Rent** 💳: Base rent + a % of sales (retail).
- **Option to Renew / Termination** 🔁: Lease flexibility provisions.
        """)

    # ─────────────────────────────────────────────────────────────────────────────
    # 📊 Data & Methodology Disclaimer
    # ─────────────────────────────────────────────────────────────────────────────
    with st.expander("📊 Data & Methodology Disclaimer"):
        st.markdown("""
**Where does the data come from?**  
All deal analyses are based on user‑provided inputs (purchase price, rent, expenses, loan terms, appreciation assumptions). The app does **not** pull live market data unless you connect third‑party sources in the future.

---

**How are projections calculated?**  
- **ROI, Cap Rate, Cash Flow** follow standard formulas.  
- **Multi‑Year ROI** includes appreciation, equity growth, and tax‑adjusted cash flow.  
- **IRR** accounts for timing of all cash flows (including sale).  
- **Depreciation** uses a 27.5‑year schedule for residential (building only).  
- **Deal Score** blends ROI, Cap Rate, and Cash Flow into a 0–100 scale.

---

**Key assumptions (editable in tools):**  
- Annual growth rates for rent/expenses.  
- Selling costs (default ~6%).  
- Monthly loan amortization.  
- Conservative defaults for rehab/refi until you customize.

---

**Disclaimer:** This tool is for **educational and estimation purposes only**. Always consult a qualified professional (agent, CPA, lender, attorney) before making investment decisions.
        """)

    st.markdown("</div>", unsafe_allow_html=True)
