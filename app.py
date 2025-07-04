import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objs as go
import numpy_financial as npf
from fpdf import FPDF
import os, json

# Load deals from file when app starts
if "deals" not in st.session_state:
    if os.path.exists("deals.json"):
        with open("deals.json", "r") as f:
            st.session_state["deals"] = json.load(f)
    else:
        st.session_state["deals"] = []

# ─────────────────────────── PAGE CONFIG ────────────────────────────
st.set_page_config(page_title="🏡 Smart Rental Analyzer", layout="wide")

# ─────────────────────────── GLOBAL STYLING ─────────────────────────
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


# ── Sticky Deal Summary Bar ──────────────────────────────────────────
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


# ─────────────────────────── TOOLTIP HELPER ─────────────────────────
TOOLTIP = """
<span class='tooltip'>[?]<span class='tooltiptext'>{}</span></span>
"""


def tt(label:str, tip:str):
    return f"**{label}** {TOOLTIP.format(tip)}"

# ─────────────────────────── HEADER / NAV ───────────────────────────
st.markdown("<h1 style='text-align:center;'>🏡 Smart Rental Analyzer</h1>", unsafe_allow_html=True)
col_l, col_c, col_r = st.columns([2.2,2,0.8])
with col_c: st.image("logo.png", width=150)
st.markdown("<p style='text-align:center; font-size:14px; color:gray;'>Created by Jacob Klingman</p>", unsafe_allow_html=True)

st.markdown("### 📬 Contact Me")
st.markdown("**Email:** [smart-rental-analyzer@outlook.com](mailto:smart-rental-analyzer@outlook.com)")

page = st.selectbox("Navigate to:", [
    "🏠 Home",
    "📊 Quick Deal Analyzer",
    "💡 Break-Even Calculator",
    "📘 ROI & Projections",
    "📂 Deal History",
    "🏘 Property Comparison",
    "🧪 Advanced Analytics (Pro)",
    "🏚 Rehab & Refi (Pro)",
    "📊 Deal Summary Comparison",
    "📖 Glossary"
])


# Chart Upgrade Helper: Use Plotly for all visuals going forward.
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


# ─────────────────────────── HOME ────────────────────────────
if page == "🏠 Home":
    st.markdown("---")
    st.markdown("<div class='card'>", unsafe_allow_html=True)

    cols = st.columns(3)
    cols[0].success("✅ Beginner Friendly")
    cols[1].info("📈 Advanced ROI Tools")
    cols[2].warning("💾 Export & Reports")

    st.markdown("---")
    st.markdown("**Features:** Quick Deal Analyzer, ROI & Projections, Break-Even, CSV/PDF Exports, Premium Pro tools")
    st.markdown("---")

    st.markdown("### 🆚 How We Stack Up Against Competitors")
    comp_data = {
        'Feature':[ 'Quick Deal Analyzer','ROI & Multi-Year Projections','Break-Even Calculator','Deal Score / Rating','Property Comparison','Advanced Analytics Charts','Rehab & Refi Tools','CSV Export','PDF Export','Mobile Friendly','AI Insights'],
        'S.R.A':['✅','✅','✅','✅','✅','✅','✅','✅','✅','✅','🚧'],
        'BiggerPockets':['✅','✅','❌','❌','❌','❌','❌','✅','❌','✅','❌'],
        'Stessa':['❌','✅','❌','❌','❌','❌','❌','✅','❌','✅','❌'],
        'Roofstock':['✅','✅','❌','❌','❌','❌','❌','✅','✅','✅','❌'],
        'DealCheck':['✅','✅','❌','❌','✅','❌','❌','✅','❌','🚧','❌'],
        'Mashvisor':['✅','✅','❌','❌','❌','✅','❌','✅','❌','✅','❌'],
        'Rentometer':['✅','❌','❌','❌','❌','❌','❌','❌','❌','✅','❌'],
        'Zilculator':['✅','✅','✅','❌','✅','❌','❌','✅','❌','❌','❌']
    }
    styled = pd.DataFrame(comp_data).set_index('Feature')
    st.dataframe(styled, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ─────────────────────────── QUICK DEAL ANALYZER ───────────────────
# 📊 QUICK DEAL ANALYZER TAB — CLEANED + DEAL SNAPSHOT INTEGRATED

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

    col1, col2 = st.columns(2)
    with col1:
        price = st.number_input("Purchase Price ($)", value=250000)
        rent = st.number_input("Monthly Rent ($)", value=2200)
    with col2:
        expenses = st.number_input("Monthly Expenses ($)", value=1400)
        down_pct = st.slider("Down Payment (%)", 0, 100, 20)

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

        roi_score = min(roi, 20) / 20 * 60  # Max 60 points
        cap_score = min(cap_rate, 10) / 10 * 30  # Max 30 points
        cf_score = 10 if annual_cf > 0 else -10
        score = max(0, min(roi_score + cap_score + cf_score, 100))

        
        st.session_state.results = {
            "cf": annual_cf,
            "roi": roi,
            "cap": cap_rate,
            "score": score,
        }

        # ✅ Save to history
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
            "tags": [],
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

        st.markdown("### 🧮 Quick Sensitivity Adjustment")
        rent_min, rent_max = int(rent * 0.8), int(rent * 1.2)
        exp_min, exp_max = int(expenses * 0.8), int(expenses * 1.2)
        col5, col6 = st.columns(2)
        with col5:
            adj_rent = st.slider("Adjusted Rent", rent_min, rent_max, rent, step=25, format="$%d")
        with col6:
            adj_exp = st.slider("Adjusted Expenses", exp_min, exp_max, expenses, step=25, format="$%d")

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



# ─────────────────────────── BREAK-EVEN CALCULATOR ────────────────
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
        price = st.number_input("Purchase Price ($)",250000)
        down_pct = st.slider("Down Payment (%)",0,100,20)
        int_rate = st.number_input("Loan Interest Rate (%)",6.5)
        term = st.selectbox("Loan Term (Years)",[15,30],index=1)
    with c2:
        ti = st.number_input("Taxes + Insurance + HOA ($/mo)",300)
        maint_pct = st.slider("Maintenance (% of Rent)",0,20,10)
        mgmt_pct = st.slider("Management (% of Rent)",0,20,8)
        vac = st.slider("Vacancy Rate (%)",0,20,5)

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
        csv=pd.DataFrame({"Rent":rng,"Cash Flow":cfs}).to_csv(index=False).encode()
        st.download_button("⬇️ Download Cash Flow Table (CSV)",csv,"break_even_cash_flow.csv","text/csv")
    else:
        st.error("❌ No break-even rent found in range. Try adjusting inputs.")
    st.markdown("</div>", unsafe_allow_html=True)

# ─────────────────────────── ROI & PROJECTIONS ────────────────────
elif page == "📘 ROI & Projections":
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.header("📘 ROI & Multi-Year Projections")
    with st.expander("📘 Key Terms"):
        c1,c2 = st.columns(2)
        with c1:
            st.markdown(tt("Equity","Value minus loan balance"),unsafe_allow_html=True)
            st.markdown(tt("Rent Growth","Annual rent increase"),unsafe_allow_html=True)
        with c2:
            st.markdown(tt("Expense Growth","Annual cost increase"),unsafe_allow_html=True)
            st.markdown(tt("Appreciation","Property value growth"),unsafe_allow_html=True)

    c1,c2 = st.columns(2)
    with c1:
        price = st.number_input("Purchase Price ($)",250000,key="roi_price")
        dpct = st.slider("Down Payment (%)",0,100,20,key="roi_dp")
        rate = st.number_input("Interest Rate (%)",6.5,key="roi_rate")
        term = st.selectbox("Loan Term (Years)",[15,30],index=1,key="roi_term")
        years = st.slider("Years to Project",1,30,5)
    with c2:
        rent = st.number_input("Starting Monthly Rent ($)",2200)
        exp = st.number_input("Monthly Expenses ($)",800)
        rent_g = st.slider("Rent Growth (%/yr)",0,10,3)
        exp_g = st.slider("Expense Growth (%/yr)",0,10,2)
        appr = st.slider("Appreciation (%/yr)",0,10,3)

    dp = price*dpct/100
    loan = price-dp
    mrate = rate/100/12
    tot_months = term*12
    mortgage = npf.pmt(mrate,tot_months,-loan)

    balance=loan; value=price; r=rent; e=exp
    rows=[]; roi_vals=[]
    for yr in range(1,years+1):
        annual_cf=(r-e-mortgage)*12
        for _ in range(12):
            intr=balance*mrate; princ=mortgage-intr; balance-=princ
        equity=value-balance
        roi=((annual_cf+equity)/dp)*100
        rows.append([yr,f"${r*12:,.0f}",f"${e*12:,.0f}",f"${annual_cf:,.0f}",f"${equity:,.0f}",f"{roi:.1f}%"])
        roi_vals.append(roi)
        r*=1+rent_g/100; e*=1+exp_g/100; value*=1+appr/100

    df=pd.DataFrame(rows,columns=["Year","Annual Rent","Annual Expenses","Cash Flow","Equity","ROI"])
    st.dataframe(df,use_container_width=True)
    st.plotly_chart(plot_line_chart("Projected ROI (%)", list(range(1,years+1)), {"ROI %": roi_vals}))
    csv=df.to_csv(index=False).encode()
    st.download_button("⬇️ Download ROI Projection (CSV)",csv,"roi_projection.csv","text/csv")
    st.markdown("</div>", unsafe_allow_html=True)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
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
            tags = ", ".join(deal.get("tags", [])) or "—"
            row("Tags", tags)
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

# ───────────────────────────────────────────────────────────────────────



# ─────────────────────────── PROPERTY COMPARISON ────────────────
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
        price = st.number_input("Purchase Price ($)", value=300000)
        rent = st.number_input("Monthly Rent ($)", value=2500)
    with col2:
        expenses = st.number_input("Monthly Expenses ($)", value=1800)
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
                st.download_button("⬇️ Download Property Comparison", data=f, file_name=path, mime="application/pdf")

    st.markdown("</div>", unsafe_allow_html=True)


# ─────────────────────────── ADVANCED ANALYTICS ──────────────────
elif page == "🧪 Advanced Analytics (Pro)":
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.header("🧪 Advanced Analytics & Forecasting (Pro)")
    scenario = st.radio("Scenario",["Conservative","Base","Aggressive","Custom"],horizontal=True)
    if scenario=="Conservative": rent_g,appr,exp_g = 1.5,2.0,3.0
    elif scenario=="Aggressive": rent_g,appr,exp_g = 4.0,5.0,1.5
    elif scenario=="Base": rent_g,appr,exp_g = 2.5,3.0,2.0
    else:
        rc1,rc2,rc3 = st.columns(3)
        with rc1: rent_g = st.number_input("Rent Growth %",2.5)
        with rc2: appr = st.number_input("Appreciation %",3.0)
        with rc3: exp_g = st.number_input("Expense Growth %",2.0)

    st.subheader("📈 5-Year Projection")
    price=250000; rent=2200; exp=800; loan=200000; rate=0.065/12; months=30*12
    mortgage=npf.pmt(rate,months,-loan)
    years=[1,2,3,4,5]; cf_list=[]; eq_list=[]; roi_list=[]; balance=loan; val=price
    for y in years:
        cf=(rent-exp-mortgage)*12
        for _ in range(12): intr=balance*rate; princ=mortgage-intr; balance-=princ
        equity=val-balance; roi=((cf+equity)/(price-loan))*100
        cf_list.append(cf); eq_list.append(equity); roi_list.append(roi)
        rent*=1+rent_g/100; exp*=1+exp_g/100; val*=1+appr/100

    fig = plot_line_chart("5-Year Investment Projections", years, {
        "Annual Cash Flow": cf_list,
        "Equity": eq_list,
        "ROI %": roi_list
    })
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ─────────────────────────── REHAB & REFI ────────────────────────
elif page == "🏚 Rehab & Refi (Pro)":
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.header("🏚 Renovation & Refinance Tools (Pro)")
    with st.expander("🛠️ Rehab ROI Calculator",expanded=True):
        r1,r2 = st.columns(2)
        with r1:
            price = st.number_input("Purchase Price ($)",300000)
            dpct = st.slider("Down Payment %",0,100,20)
            dp = price*dpct/100
            rehab = st.number_input("Rehab Cost ($)",25000,step=1000)
        with r2:
            loan_bal = st.number_input("Outstanding Loan Balance ($)",int(price-dp))
            arv = st.number_input("After-Repair Value ($)",int(price*1.1),step=1000)
            months = st.slider("Months Until Rehab Complete",1,24,6)
        invested=dp+rehab; equity=arv-loan_bal; post_roi=((equity-invested)/invested)*100 if invested else 0
        st.metric("Total Invested",f"${invested:,.0f}"); st.metric("Equity After Rehab",f"${equity:,.0f}"); st.metric("Post-Rehab ROI",f"{post_roi:.1f}%")

    with st.expander("🔄 Refinance Explorer",expanded=False):
        c1,c2 = st.columns(2)
        with c1:
            refi_after = st.slider("Refinance After (Months)",1,360,12)
            new_rate = st.number_input("New Rate (%)",5.0)
        with c2:
            new_term = st.selectbox("New Term (Years)",[15,20,30],2)
            cash_out = st.number_input("Cash-Out ($)",0,step=1000)
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

            # Emoji helpers (with float conversion)
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

            # Data rows with emoji indicators
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



# ─────────────────────────── GLOSSARY ───────────────────────────
elif page == "📖 Glossary":
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.header("📖 Real Estate & Investment Glossary")
    glossary={
        "Appraisal":"Professional estimate of market value.",
        "Cap Rate":"NOI ÷ Purchase Price.",
        "Cash Flow":"Money left each month after expenses.",
        "Cash on Cash Return":"Annual cash flow ÷ cash invested.",
        "Closing Costs":"One-time fees at purchase.",
        "Comps":"Comparable recent sales.",
        "Depreciation":"Tax deduction spreading property cost.",
        "Equity":"Value minus loan balance.",
        "Gross Rent Multiplier":"Price ÷ Gross Annual Rent.",
        "Hard Money Loan":"Short-term, high-interest loan.",
        "HOA":"Homeowners Association fee.",
        "IRR":"Internal Rate of Return over time.",
        "Loan-to-Value":"Loan amount ÷ property value.",
        "Maintenance":"Reserve % of rent for repairs.",
        "Net Operating Income":"Rent minus operating expenses.",
        "PMI":"Private Mortgage Insurance.",
        "Vacancy Rate":"% time property is vacant."
    }
    for k in sorted(glossary.keys()): st.markdown(f"**{k}**: {glossary[k]}")
    st.markdown("</div>", unsafe_allow_html=True)


