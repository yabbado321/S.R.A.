import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objs as go
import numpy_financial as npf
from fpdf import FPDF
import os, json
import requests

from datetime import datetime

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
st.set_page_config(page_title="🏡 Smart Rental Analyzer", layout="wide")

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
    "📂 Deal History",
    "🏘 Property Comparison",
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
    "📂 Deal History",
    "🏘 Property Comparison",
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
        'Property Comparison',
        'Advanced Analytics',
        'Monte Carlo Simulator',
        'Rehab & Refi Tools',
        'Tax Benefits Explorer',
        'CSV Export',
        'PDF Export',
        'Deal History & Notes',
        'Score System (0–100 w/ Tips)',
        'Mobile Friendly',
    ],
    'RentIntel': ['✅'] * 13 ,
    'BiggerPockets': ['✅', '✅', '❌', '❌', '❌', '❌', '❌', '❌', '✅', '❌', '❌', '❌', '✅', ],
    'Stessa':        ['❌', '✅', '❌', '❌', '❌', '❌', '❌', '✅', '✅', '❌', '❌', '❌', '✅', ],
    'Roofstock':     ['✅', '✅', '❌', '❌', '❌', '❌', '❌', '❌', '✅', '✅', '❌', '❌', '✅', ],
    'DealCheck':     ['✅', '✅', '❌', '✅', '❌', '❌', '❌', '❌', '✅', '❌', '❌', '❌', '🚧', ],
    'Mashvisor':     ['✅', '✅', '❌', '❌', '✅', '❌', '❌', '❌', '✅', '❌', '❌', '❌', '✅', ],
    'Rentometer':    ['✅', '❌', '❌', '❌', '❌', '❌', '❌', '❌', '❌', '❌', '❌', '❌', '✅', ],
    'Zilculator':    ['✅', '✅', '✅', '✅', '❌', '❌', '❌', '❌', '✅', '❌', '❌', '❌', '❌', ]
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

        # Editable Assumptions
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

        # Calculations
        ti_month = price * (ti_pct / 100) / 12
        maint = rent * (maint_pct / 100)
        mgmt = rent * (mgmt_pct / 100)
        vacancy = rent * (vac_pct / 100)

        loan_amt = price * (1 - down_pct / 100)
        mort_rate = 0.065 / 12  # fixed est. 6.5%
        mortgage = loan_amt * mort_rate

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

        # Optional Text Export
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
        for r in range(500,5000,10):
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

    # New inputs for tax & sale
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

        # Amortize loan balance monthly for the year
        for _ in range(12):
            interest = balance * mrate
            principal = mortgage - interest
            balance -= principal

        # Appreciation applies at end of year
        value *= (1 + appr / 100)

        # Equity gain excludes initial down payment
        equity = (value - balance) - dp

        # Depreciation calculation (building value / 27.5 years)
        building_value = price * (1 - land_pct / 100)
        annual_depr = building_value / 27.5

        # Tax savings from depreciation (simplified)
        tax_savings = annual_depr * tax_rate / 100

        # After-tax cash flow = cash flow + tax savings (simplified)
        after_tax_cf = annual_cf + tax_savings

        # ROI calculations
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

        # Increase rent and expenses for next year
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
        # Build cash flow array for IRR: initial investment (negative), then yearly after-tax cash flow,
        # then sale proceeds at sale_year with equity + sale appreciation minus 6% selling costs

        initial_outflow = -dp
        cash_flows = [initial_outflow]
        # Use after-tax cash flow for each year except sale year
        for y in range(1, years + 1):
            if y == sale_year:
                # Sale proceeds = equity at sale year + remaining equity from principal + appreciation
                # subtract 6% selling costs on property value at sale
                prop_value_at_sale = price * ((1 + appr / 100) ** y)
                selling_costs = prop_value_at_sale * 0.06
                net_sale_proceeds = equity_list[y-1] + dp - selling_costs  # include original down payment back
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

        # Export button per category
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
    import pandas as pd
    from fpdf import FPDF

    def comparison_to_pdf(df):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "Property Comparison Report", ln=True)
        pdf.ln(5)

        pdf.set_font("Arial", '', 10)
        for idx, row in df.iterrows():
            pdf.set_fill_color(240, 240, 240)
            pdf.cell(0, 8, f"🏠 {row['Property Name']}", ln=True, fill=True)
            for key in ["Purchase Price", "Monthly Rent", "Monthly Expenses", "Cash Flow", "Cap Rate", "ROI", "Score"]:
                val = row.get(key, '-')
                if isinstance(val, float):
                    val = f"{val:,.2f}" if not key.endswith("Rate") and key != "Score" else f"{val:.1f}%"
                elif isinstance(val, int):
                    val = f"${val:,}" if "Price" in key or "Rent" in key or "Expenses" in key or "Cash Flow" in key else str(val)
                pdf.cell(60, 8, f"{key}:", border=0)
                pdf.cell(0, 8, str(val), ln=True)
            pdf.ln(4)

        filename = "property_comparison.pdf"
        pdf.output(filename)
        return filename

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.header("🏘 Property Comparison Tool")
    st.caption("Compare multiple properties side-by-side.")

    if "comparison_inputs" not in st.session_state:
        st.session_state.comparison_inputs = []

    st.markdown("### 🏠 Add Property Inputs")
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Property Name", value="123 Main St")
        price = st.number_input("Purchase Price ($)", min_value=-1e6, value=300000.0)
        rent = st.number_input("Monthly Rent ($)", min_value=-1e6, value=2500.0)
    with col2:
        expenses = st.number_input("Monthly Expenses ($)", min_value=-1e6, value=1800.0)
        down = st.slider("Down Payment %", 0, 100, 20)

    if st.button("➕ Add to Compare"):
        st.session_state.comparison_inputs.append({
            "Property Name": name,
            "Purchase Price": price,
            "Monthly Rent": rent,
            "Monthly Expenses": expenses,
            "Down Payment": down
        })
        st.success(f"Added {name} to comparison list")

    st.markdown("### 🗂 Current Properties")
    for i, prop in enumerate(st.session_state.comparison_inputs):
        col1, col2 = st.columns([6, 1])
        with col1:
            st.markdown(f"**🏠 {prop['Property Name']}** - ${prop['Purchase Price']:,} | Rent: ${prop['Monthly Rent']:,} | Expenses: ${prop['Monthly Expenses']:,} | Down: {prop['Down Payment']}%")
        with col2:
            if st.button("❌ Delete", key=f"delete_comp_{i}"):
                st.session_state.comparison_inputs.pop(i)
                st.rerun()

    if st.button("📊 Compare Properties") and st.session_state.comparison_inputs:
        df_data = []
        for prop in st.session_state.comparison_inputs:
            price = prop["Purchase Price"]
            rent = prop["Monthly Rent"]
            expenses = prop["Monthly Expenses"]
            down = prop["Down Payment"]
            annual_cf = (rent - expenses) * 12
            down_amt = price * down / 100
            roi = (annual_cf / down_amt) * 100 if down_amt else 0
            cap = (annual_cf / price) * 100 if price else 0

            roi_score = min(roi / 20 * 30, 30)
            cf_score = min((rent - expenses) / 300 * 30, 30)
            cap_score = min(cap / 10 * 20, 20)
            bonus = 10 if roi > 10 and (rent - expenses) > 250 else 0
            deal_score = roi_score + cf_score + cap_score + bonus

            df_data.append({
                **prop,
                "Cash Flow": rent - expenses,
                "Cap Rate": cap,
                "ROI": roi,
                "Score": deal_score
            })

        comparison_df = pd.DataFrame(df_data)
        st.markdown("### 📋 Comparison Results")
        st.dataframe(comparison_df, use_container_width=True)

        if st.button("📄 Export Comparison to PDF"):
            path = comparison_to_pdf(comparison_df)
            with open(path, "rb") as f:
               csv = export_csv_with_watermark(comparison_df)
               st.download_button("⬇️ Download Comparison Table", csv, "comparison.csv", "text/csv")


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
    cash_flows = [-down]  # Initial investment as negative cash flow

    for y in years:
        # Annual cash flow calculation
        cf = (r - e - mortgage) * 12

        principal_paid_year = 0
        # Monthly amortization
        for _ in range(12):
            interest = balance * m_rate
            principal = mortgage - interest
            balance -= principal
            principal_paid_year += principal

        # Update property value with appreciation
        val *= 1 + appr / 100

        # Equity = current value minus remaining loan balance
        equity = val - balance

        # ROI calculation (total return relative to down payment)
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

        # Increase rent and expenses for next year
        r *= 1 + rent_g / 100
        e *= 1 + exp_g / 100

    # Calculate net proceeds from sale at exit
    sale_price = val
    selling_costs = 0.06 * sale_price
    net_sale_proceeds = sale_price - selling_costs - balance

    # Append sale proceeds to cash flows for IRR calc
    cash_flows[-1] += net_sale_proceeds  # Add sale proceeds to last year cash flow

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
    import re
    from fpdf import FPDF

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.header("💸 Rental Property Tax Benefits & Write-Offs")
    st.markdown("Explore the deductions available to landlords — with IRS links and audit tips to keep you protected.")
    st.header("IMPORTANT DISCLAIMER!")
    st.markdown("""
    Disclaimer: This tool is for educational and estimation purposes only. Always consult a qualified professional (real estate agent, CPA, lender) before making investment decisions.

 Record-Keeping: It’s crucial to maintain detailed records of all your rental property expenses and keep receipts.

 Capitalization vs. Expense: Distinguish between repairs (deductible in the year incurred) and improvements (which must be capitalized and depreciated).

 Tax Professional: Consider consulting a tax professional to ensure you’re taking full advantage of all eligible deductions""")
    benefits = [
        ("🏦 Mortgage Interest Deduction - IRS Section 163(h)",
         "Deduct interest paid on loans for purchasing, refinancing, or improving rental properties.",
         "https://www.irs.gov/publications/p936",
         "Keep copies of your loan documents and annual Form 1098 from your lender."),
        
        ("🏠 Property Taxes - IRS Section 164",
         "Deduct real estate taxes paid to local and state governments.",
         "https://www.irs.gov/taxtopics/tc503",
         "Keep property tax bills and proof of payment (e.g., bank statements or checks)."),
        
        ("📉 Depreciation - IRS Section 167 & 168",
         "You can depreciate the building (not land) over 27.5 years — reducing taxable income even as the property appreciates.",
         "https://www.irs.gov/publications/p527#en_US_2023_publink1000219031",
         "Maintain records of the purchase price, land vs building value, and depreciation schedules."),
        
        ("🔧 Repairs & Maintenance - IRS Section 162",
         "Deduct repairs like plumbing fixes, painting, or replacing appliances — not improvements.",
         "https://www.irs.gov/publications/p527#en_US_2023_publink1000219043",
         "Save all repair receipts and make a note of the purpose and date of the work."),
        
        ("🛡️ Insurance Premiums - IRS Section 162",
         "Landlord, liability, flood, and fire insurance premiums are fully deductible.",
         "https://www.irs.gov/publications/p535",
         "Keep annual insurance invoices and proof of payment."),
        
        ("👨‍💼 Property Management Fees - IRS Section 162",
         "Fees paid to property managers or assistants for running rental operations are deductible.",
         "https://www.irs.gov/publications/p527#en_US_2023_publink1000219044",
         "Retain management agreements, invoices, and payment confirmations."),
        
        ("🚗 Travel & Mileage - IRS Section 162",
         "Deduct trips made for rental purposes — mileage, lodging, or airfare if the property is out of town.",
         "https://www.irs.gov/pub/irs-pdf/p463.pdf",
         "Use a mileage log app or notebook. Record trip dates, purpose, and distances."),
        
        ("⚖️ Legal & Professional Fees - IRS Section 162",
         "Deduct legal advice, eviction filings, accounting, and tax prep fees for rentals.",
         "https://www.irs.gov/publications/p535",
         "Save all invoices and retainers, especially for legal work."),
        
        ("💡 Utilities - IRS Section 162",
         "Landlord-paid gas, water, electric, internet, and trash are deductible.",
         "https://www.irs.gov/publications/p527#en_US_2023_publink1000219044",
         "Keep utility bills and statements. Note which units each bill covers."),
        
        ("📢 Advertising & Tenant Screening - IRS Section 162",
         "Deduct rental listings, signs, flyers, and screening services (credit/background checks).",
         "https://www.irs.gov/publications/p527#en_US_2023_publink1000219044",
         "Save invoices from listing platforms and screening services."),
        
        ("🏘 HOA Fees & Condo Dues - IRS Section 162",
         "Monthly or annual HOA/condo fees related to rental units are deductible.",
         "https://www.irs.gov/publications/p527#en_US_2023_publink1000219044",
         "Save HOA billing statements and bank records of payments."),
        
        ("🧰 Supplies & Small Tools - IRS Section 162",
         "Items like locks, smoke detectors, cleaning supplies, or light tools are deductible.",
         "https://www.irs.gov/publications/p535",
         "Keep itemized receipts and note which property each supply was used for."),
        
        ("🏡 Home Office Deduction - IRS Section 280A",
         "If you manage rentals from a dedicated space at home, you may qualify for this deduction.",
         "https://www.irs.gov/publications/p587",
         "Document square footage, take photos of the space, and keep utility/home bills."),
        
        ("📚 Education & Books -  IRS Section 162",
         "Courses, seminars, or books that enhance your rental property management skills may be deductible.",
         "https://www.irs.gov/publications/p970",
         "Keep receipts and ensure the content is directly related to your rental business."),
        
        ("🚀 Start-Up & Organizational Costs - IRS Section 195",
         "Initial legal, research, and marketing costs before your first rental goes live can be amortized.",
         "https://www.irs.gov/publications/p535#en_US_2023_publink1000208932",
         "Document each startup expense and note the date your rental officially began.")
    ]

    for title, desc, link, tip in benefits:
        with st.expander(title):
            st.markdown(f"**What It Is:** {desc}")
            st.markdown(f"🔗 [IRS Guidance]({link})")
            st.markdown(f"🧾 **Audit Tip:** {tip}")


    st.markdown("</div>", unsafe_allow_html=True)

# ─────────────────────────── GLOSSARY ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
elif page == "📖 Help & Info":
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.header("📖 Real Estate Glossary & Methodology")
    st.markdown("*A beginner-friendly guide to key real estate terms and how our estimates work.*")

    with st.expander("💰 Cash Flow & Returns"):
        st.markdown("""
- **Cash Flow** 📈: Money left over each month after paying all expenses.
- **ROI (Return on Investment)** 💸: Your profit as a % of the money you invested.
- **Cap Rate** 🏦: Return based only on property income (ignores loan); higher is better.
- **IRR (Internal Rate of Return)** ⏳: Average yearly return over time, with timing factored in.
- **Cash-on-Cash Return** 💵: Cash profit ÷ cash invested — helpful when using loans.
- **Equity** 💎: What you “own” in the property = value minus loan.
- **Appreciation** 📈: Increase in property value over time.
- **Net Operating Income (NOI)** 🧮: Rent - expenses (excluding mortgage).
- **Total Return** 🧾: All gains combined — cash flow + equity + appreciation.
        """)

    with st.expander("🏠 Property Terms"):
        st.markdown("""
- **Purchase Price** 💲: What you pay to buy the property.
- **After Repair Value (ARV)** 🛠: Estimated value after rehab/renovations.
- **Comparable Sales (Comps)** 🏘: Similar recently sold properties used to estimate value.
- **Square Footage (Sq Ft)** 📏: The size of the home or unit.
- **Zoning** 🧭: Local rules that control how the property can be used (e.g. residential, multifamily).
- **HOA (Homeowners Association)** 🏘️: Monthly fees for shared communities or condos.
        """)

    with st.expander("📊 Deal Analysis Metrics"):
        st.markdown("""
- **Gross Rent Multiplier (GRM)** 📐: Price ÷ Gross Annual Rent — a fast value estimate.
- **Break-Even Rent** 💡: Minimum rent needed to cover all costs.
- **Occupancy Rate** 🛏️: How often the property is rented out (vs. vacant).
- **Vacancy Rate** 🚪: % of time the property is not rented.
- **Deal Score** 🧠: A 0–100 score in RentIntel to help rank your deals.
        """)

    with st.expander("📉 Financing & Mortgages"):
        st.markdown("""
- **Down Payment** 💳: The cash you put up front (usually 20%).
- **Loan-to-Value (LTV)** 📊: Loan ÷ Property Value — helps lenders assess risk.
- **Interest Rate** 📈: What the lender charges you to borrow money.
- **Mortgage** 🏦: A loan used to buy real estate, paid monthly over time.
- **Amortization** ⏱️: The way your loan balance goes down monthly.
- **Private Mortgage Insurance (PMI)** 🛡️: Extra insurance if your down payment is under 20%.
- **Hard Money Loan** 🔥: Short-term, high-interest loan (used for flips or fast deals).
- **Refinancing** 🔄: Replacing your loan with a new one — often to pull cash or lower rates.
        """)

    with st.expander("🧾 Taxes & Write-Offs"):
        st.markdown("""
- **Depreciation** 📉: A tax benefit that lets you deduct the building’s value over 27.5 years.
- **Tax Savings** 🧾: Money you save at tax time due to expenses, depreciation, etc.
- **1031 Exchange** 🔄: A way to sell a property and buy another without paying taxes now.
- **Property Taxes** 🏠: Annual taxes paid to your city or county.
- **IRS Schedule E** 📄: The tax form used to report rental income and expenses.
- **Audit Trail** 📚: Proof (receipts, logs) that support your tax deductions.
        """)

    with st.expander("🧰 Operating Expenses & Management"):
        st.markdown("""
- **Repairs vs. Improvements** 🛠️: Repairs are deductible now; improvements are depreciated over time.
- **Property Management Fees** 👷: What you pay a manager to handle tenants and maintenance.
- **Maintenance Reserve** 🔧: A % of rent saved for ongoing repairs.
- **Capital Expenditures (CapEx)** 🧱: Big-ticket items like roofs, HVAC, etc.
- **Utilities** 💡: Landlord-paid services like water, gas, electric, etc.
- **Insurance Premiums** 🛡️: Coverage for fire, liability, flood, etc.
        """)

    with st.expander("🧠 Strategy Terms"):
        st.markdown("""
- **BRRRR** 🔁: Buy, Rehab, Rent, Refinance, Repeat — a strategy to build a portfolio with less money.
- **Buy & Hold** 🏠: Long-term rental investing for cash flow and appreciation.
- **Fix & Flip** 🔨: Buy low, rehab fast, and sell for profit.
- **House Hacking** 🧍🏠: Living in one part of a property and renting the rest.
- **Wholesale Deal** 📦: Assigning a contract to another buyer for a fee.
        """)

    with st.expander("📊 Data & Methodology Disclaimer"):
        st.markdown("""
**Where does the data come from?**  
All deal analyses are based on user-provided inputs like purchase price, rent, expenses, loan terms, and appreciation assumptions. The app does **not pull live market data** (e.g. Zillow, MLS, or county records) unless connected to third-party sources in the future.

---

**How are projections calculated?**  
- **ROI, Cap Rate, and Cash Flow** use standard industry formulas.
- **Multi-Year ROI** includes appreciation, equity growth, and tax-adjusted cash flow.
- **IRR (Internal Rate of Return)** accounts for the timing of all cash flows.
- **Depreciation** is calculated on a 27.5-year schedule (per IRS).
- **Deal Score** is a RentIntel formula blending ROI, Cap Rate, and Cash Flow into a 0–100 score.

---

**What assumptions are included?**  
- Rent and expense growth are applied annually.
- Selling costs are assumed to be 6% of resale price.
- Loan amortization is based on monthly payments.
- Rehab/refi assumptions are conservative by default.

---

**Disclaimer:** This tool is for **educational and estimation purposes only**. Always consult a qualified professional (real estate agent, CPA, lender) before making investment decisions.
        """)

    st.markdown("</div>", unsafe_allow_html=True)
