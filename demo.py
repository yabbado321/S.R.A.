# mobile_app.py (Mobile-Optimized Version with Core Tabs)
import streamlit as st
import numpy_financial as npf
import numpy as np
import pandas as pd

st.set_page_config(page_title="📱 Mobile Rental Analyzer", layout="centered")

# ───────────── STYLES ─────────────
st.markdown("""
<style>
body { background-color: #18181b; color: #f3f3f3; }
.stButton>button {
  background: #4ade80;
  color: #000;
  border-radius: 12px;
  font-size: 1rem;
  padding: 0.75rem 1.5rem;
  margin-top: 1rem;
  width: 100%;
}
input, textarea {
  background-color: #2a2a2a !important;
  color: #f3f3f3 !important;
  border-radius: 6px !important;
}
@media only screen and (max-width: 768px) {
  h1 { font-size: 1.5rem; }
  .stButton>button { font-size: 1rem; padding: 0.75rem 1.25rem; }
  .stTextInput input, .stNumberInput input { font-size: 1rem; }
}
</style>
""", unsafe_allow_html=True)

st.title("📱 *BETA* Smart Rental Analyzer (Mobile)")
st.caption("Quick tools for real estate investors on the go")

# ───────────── TABS ─────────────
tab = st.selectbox("🔎 Choose Tool", [
    "📊 Quick Deal Analyzer",
    "💡 Break-Even Calculator",
    "📘 ROI Projection",
    "📬 Contact"
])

# ───────────── QUICK DEAL ANALYZER ─────────────
if tab == "📊 Quick Deal Analyzer":
    st.subheader("📊 Quick Deal Analyzer")
    name = st.text_input("Property Name", value="123 Mobile Ave")
    price = st.number_input("Purchase Price ($)", value=250000.0)
    rent = st.number_input("Monthly Rent ($)", value=2200.0)
    expenses = st.number_input("Monthly Expenses ($)", value=1400.0)
    down_pct = st.slider("Down Payment (%)", 0, 100, 20)

    if st.button("🔍 Analyze Deal"):
        invest = price * down_pct / 100
        annual_cf = (rent - expenses) * 12
        roi = (annual_cf / invest) * 100 if invest else 0
        cap = ((rent - expenses) * 12 / price) * 100 if price else 0

        score = min(roi, 20)/20*60 + min(cap, 10)/10*30 + (10 if annual_cf > 0 else -10)
        score = max(0, min(score, 100))

        st.metric("ROI", f"{roi:.1f}%")
        st.metric("Cap Rate", f"{cap:.1f}%")
        st.metric("Cash Flow", f"${annual_cf:,.0f}")
        st.metric("Score", f"{score:.1f}/100")

        st.markdown("### 💡 Tips")
        if roi < 10:
            st.markdown("• Try increasing rent or lowering expenses.")
        if cap < 5:
            st.markdown("• Consider negotiating a better price.")
        if annual_cf < 0:
            st.markdown("• Negative cash flow — risky deal.")

# ───────────── BREAK-EVEN CALCULATOR ─────────────
elif tab == "💡 Break-Even Calculator":
    st.subheader("💡 Break-Even Rent")
    price = st.number_input("Purchase Price ($)", value=250000.0)
    down = st.slider("Down Payment (%)", 0, 100, 20)
    int_rate = st.number_input("Loan Interest Rate (%)", value=6.5)
    term = st.selectbox("Loan Term (Years)", [15, 30], index=1)
    ti = st.number_input("Taxes + Insurance + HOA ($/mo)", value=300.0)
    maint_pct = st.slider("Maintenance (% of Rent)", 0, 50, 10)
    mgmt_pct = st.slider("Management (% of Rent)", 0, 50, 8)
    vac = st.slider("Vacancy Rate (%)", 0, 30, 5)

    loan = price * (1 - down / 100)
    m_int = int_rate / 100 / 12
    months = term * 12
    mortgage = npf.pmt(m_int, months, -loan) if loan > 0 else 0

    def find_breakeven():
        for r in range(500, 5000, 10):
            maint = r * maint_pct / 100
            mgmt = r * mgmt_pct / 100
            vac_loss = r * vac / 100
            exp = ti + maint + mgmt + vac_loss
            cf = r - (mortgage + exp)
            if cf >= 0:
                return r
        return None

    breakeven = find_breakeven()
    if breakeven:
        st.success(f"Break-Even Rent: ${breakeven:,.0f}/mo")
        st.metric("Mortgage", f"${mortgage:,.0f}/mo")
    else:
        st.error("No break-even found. Try adjusting inputs.")

# ───────────── ROI PROJECTION ─────────────
elif tab == "📘 ROI Projection":
    st.subheader("📘 Multi-Year ROI")
    price = st.number_input("Price ($)", 0.0, 1e9, 250000.0)
    dpct = st.slider("Down Payment (%)", 0.0, 100.0, 20.0)
    rate = st.number_input("Interest Rate (%)", 0.0, 20.0, 6.5)
    term = st.selectbox("Loan Term (Years)", [15, 30], index=1)
    years = st.slider("Years to Project", 1, 30, 5)

    rent = st.number_input("Starting Rent ($/mo)", 0.0, 1e5, 2200.0)
    exp = st.number_input("Monthly Expenses ($)", 0.0, 1e5, 800.0)
    rent_g = st.slider("Rent Growth (%/yr)", 0.0, 10.0, 3.0)
    exp_g = st.slider("Expense Growth (%/yr)", 0.0, 10.0, 2.0)
    appr = st.slider("Appreciation (%/yr)", 0.0, 10.0, 3.0)

    dp = price * dpct / 100
    loan = price - dp
    mrate = rate / 100 / 12
    tot_months = term * 12
    mortgage = npf.pmt(mrate, tot_months, -loan)

    balance = loan
    value = price
    r = rent
    e = exp

    roi_list = []
    for yr in range(1, years + 1):
        annual_cf = (r - e - mortgage) * 12
        for _ in range(12):
            interest = balance * mrate
            principal = mortgage - interest
            balance -= principal
        value *= (1 + appr / 100)
        equity = value - balance
        roi = ((annual_cf + equity - dp) / dp) * 100 if dp else 0
        roi_list.append((yr, f"{roi:.1f}%", f"${annual_cf:,.0f}", f"${equity:,.0f}"))
        r *= (1 + rent_g / 100)
        e *= (1 + exp_g / 100)

    st.markdown("### 📈 Projected ROI Table")
    df = pd.DataFrame(roi_list, columns=["Year", "ROI %", "Cash Flow", "Equity"])
    st.dataframe(df, use_container_width=True)

# ───────────── CONTACT ─────────────
elif tab == "📬 Contact":
    st.subheader("📬 Contact")
    st.markdown("Email: [smart-rental-analyzer@outlook.com](mailto:smart-rental-analyzer@outlook.com)")
    st.markdown("Created by Jacob Klingman")
