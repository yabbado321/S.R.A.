import streamlit as st
import numpy as np
import pandas as pd
import numpy_financial as npf

st.set_page_config(page_title="📱 Mobile Rental Analyzer", layout="wide")

# --- Title and Logo ---
st.markdown("""
<style>
body { background-color: #1e1e1e; color: white; font-family: 'Segoe UI', sans-serif; }
.button { background-color: #4caf50; border: none; padding: 10px 20px; border-radius: 8px; color: white; }
</style>
""", unsafe_allow_html=True)

st.title("📱 (LITE)Smart Rental Analyzer - Mobile Edition")
st.markdown("<p style='color:gray'>Optimized for smartphones and small screens to get full calculations use the desktop version</p>", unsafe_allow_html=True)

st.markdown("---")

page = st.selectbox("Choose Tool", [
    "Quick Deal Analyzer",
    "Break-Even Calculator",
    "ROI Projections",
    "Glossary"
])

# ---------------------- QUICK DEAL ANALYZER ----------------------
if page == "Quick Deal Analyzer":
    st.header("📊 Quick Deal Analyzer")
    st.markdown("Analyze your deal with minimal inputs.")

    purchase_price = st.number_input("Purchase Price ($)", value=250000)
    monthly_rent = st.number_input("Monthly Rent ($)", value=2200)
    monthly_expenses = st.number_input("Monthly Expenses ($)", value=1400)
    down_payment_pct = st.slider("Down Payment (%)", 0, 100, 20)

    down_payment = purchase_price * down_payment_pct / 100
    annual_cashflow = (monthly_rent - monthly_expenses) * 12
    roi = (annual_cashflow / down_payment) * 100 if down_payment else 0
    cap_rate = (annual_cashflow / purchase_price) * 100 if purchase_price else 0

    deal_score = min(roi / 20 * 40, 40) + min((monthly_rent - monthly_expenses) / 400 * 40, 40) + min(cap_rate / 10 * 20, 20)

    st.metric("Deal Score (0–100)", f"{deal_score:.1f}")
    st.metric("ROI (%)", f"{roi:.1f}%")
    st.metric("Cap Rate (%)", f"{cap_rate:.1f}%")
    st.metric("Monthly Cash Flow", f"${monthly_rent - monthly_expenses:,.0f}")

# ---------------------- BREAK-EVEN CALCULATOR ----------------------
elif page == "Break-Even Calculator":
    st.header("💡 Break-Even Rent Calculator")
    purchase_price = st.number_input("Purchase Price ($)", value=250000)
    down_payment_pct = st.slider("Down Payment (%)", 0, 100, 20)
    interest_rate = st.number_input("Loan Interest Rate (%)", value=6.5)
    loan_term = st.selectbox("Loan Term (Years)", [15, 30])
    taxes_insurance = st.number_input("Taxes + Insurance ($/mo)", value=300)
    maintenance_pct = st.slider("Maintenance (% of Rent)", 0, 20, 10)
    management_pct = st.slider("Management (% of Rent)", 0, 20, 8)
    vacancy_rate = st.slider("Vacancy Rate (%)", 0, 20, 5)

    loan_amount = purchase_price * (1 - down_payment_pct / 100)
    monthly_interest = interest_rate / 100 / 12
    months = loan_term * 12
    mortgage_payment = npf.pmt(monthly_interest, months, -loan_amount)

    def calc_break_even():
        for rent in range(500, 5000, 10):
            m = rent * (maintenance_pct / 100)
            mgmt = rent * (management_pct / 100)
            vacancy = rent * (vacancy_rate / 100)
            total_exp = taxes_insurance + m + mgmt + vacancy
            if rent - total_exp - mortgage_payment >= 0:
                return rent
        return None

    breakeven = calc_break_even()
    if breakeven:
        st.success(f"Break-Even Rent: ${breakeven:,.0f}/mo")
        st.metric("Mortgage Payment", f"${mortgage_payment:,.0f}/mo")
    else:
        st.error("No break-even found. Try adjusting inputs.")

# ---------------------- ROI PROJECTIONS ----------------------
elif page == "ROI Projections":
    st.header("📘 Multi-Year ROI Projections")

    purchase_price = st.number_input("Purchase Price ($)", value=250000)
    down_pct = st.slider("Down Payment (%)", 0, 100, 20)
    interest = st.number_input("Interest Rate (%)", value=6.5)
    loan_term = st.selectbox("Loan Term", [15, 30])
    rent = st.number_input("Starting Rent ($/mo)", value=2200)
    expenses = st.number_input("Monthly Expenses ($)", value=800)
    years = st.slider("Years to Project", 1, 30, 5)
    rent_growth = st.slider("Rent Growth (%/yr)", 0, 10, 3)
    exp_growth = st.slider("Expense Growth (%/yr)", 0, 10, 2)
    appreciation = st.slider("Property Appreciation (%/yr)", 0, 10, 3)

    down = purchase_price * down_pct / 100
    loan = purchase_price - down
    mi = interest / 100 / 12
    months = loan_term * 12
    mort = npf.pmt(mi, months, -loan)

    bal = loan
    val = purchase_price
    rows = []

    for y in range(1, years+1):
        ann_cf = (rent - expenses - mort) * 12
        for _ in range(12):
            int_paid = bal * mi
            principal = mort - int_paid
            bal -= principal
        equity = val - bal
        roi = ((ann_cf + equity) / down) * 100
        rows.append([y, f"${ann_cf:,.0f}", f"${equity:,.0f}", f"{roi:.1f}%"])

        rent *= (1 + rent_growth / 100)
        expenses *= (1 + exp_growth / 100)
        val *= (1 + appreciation / 100)

    df = pd.DataFrame(rows, columns=["Year", "Cash Flow", "Equity", "ROI"])
    st.dataframe(df, use_container_width=True)

# ---------------------- GLOSSARY ----------------------
elif page == "Glossary":
    st.header("📖 Glossary")
    terms = {
        "Cap Rate": "Net Operating Income ÷ Purchase Price",
        "Cash Flow": "Income minus all expenses.",
        "ROI": "Return on Investment including equity gain.",
        "Equity": "Value minus loan balance.",
        "Vacancy Rate": "% of time property is unoccupied.",
        "Loan-to-Value": "Loan / Property Value",
        "Appreciation": "Annual property value growth."
    }
    for t, d in terms.items():
        st.markdown(f"**{t}**: {d}")