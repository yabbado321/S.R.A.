
import streamlit as st
import json
import os
from fpdf import FPDF

st.set_page_config(page_title="Smart Rental Analyzer Mobile", layout="centered")

st.markdown("""
    <style>
    .big-font { font-size: 22px !important; }
    .stButton>button {
        padding: 0.75rem 1.5rem;
        font-size: 18px;
        border-radius: 10px;
    }
    .stTextInput>div>div>input {
        font-size: 18px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📱 Smart Rental Analyzer (Mobile)")
st.caption("Quick analysis tool optimized for mobile users.")

st.header("🔍 Quick Deal Analyzer")

with st.form("quick_analyze_mobile"):
    st.subheader("Property Basics")
    title = st.text_input("Property Title", value="Untitled Deal")
    price = st.number_input("Purchase Price ($)", min_value=0, step=1000)
    rent = st.number_input("Monthly Rent ($)", min_value=0, step=100)
    expenses = st.number_input("Monthly Expenses ($)", min_value=0, step=50)
    down_payment = st.slider("Down Payment (%)", 0, 100, 20)
    interest_rate = st.slider("Interest Rate (%)", 0.0, 10.0, 6.5, 0.1)
    loan_years = st.slider("Loan Term (Years)", 5, 40, 30)

    submitted = st.form_submit_button("💡 Analyze Deal")

if submitted:
    loan_amount = price * (1 - down_payment / 100)
    monthly_rate = interest_rate / 100 / 12
    months = loan_years * 12
    if monthly_rate > 0:
        mortgage = loan_amount * (monthly_rate * (1 + monthly_rate) ** months) / ((1 + monthly_rate) ** months - 1)
    else:
        mortgage = loan_amount / months

    total_monthly = expenses + mortgage
    cash_flow = rent - total_monthly
    annual_cf = cash_flow * 12
    total_investment = price * down_payment / 100
    roi = (annual_cf / total_investment) * 100 if total_investment > 0 else 0
    cap_rate = ((rent - expenses) * 12 / price) * 100 if price > 0 else 0
    score = (roi * 0.6 + cap_rate * 0.3 + (1 if cash_flow > 0 else -1) * 10)
    score = max(0, min(score, 100))

    st.success("✅ Deal Analyzed")
    st.metric("Monthly Cash Flow", f"${cash_flow:,.0f}")
    st.metric("ROI", f"{roi:.1f}%")
    st.metric("Cap Rate", f"{cap_rate:.1f}%")
    st.metric("Deal Score", f"{score:.0f}/100")

    st.session_state.last_result = {
        "title": title,
        "price": price,
        "rent": rent,
        "expenses": expenses,
        "roi": f"{roi:.1f}",
        "cap": f"{cap_rate:.1f}",
        "cf": cash_flow,
        "score": f"{score:.0f}",
        "type": "Quick Analyze",
        "tags": [],
        "notes": "",
        "status": "🔍 Reviewing"
    }

    if "deals" not in st.session_state:
        if os.path.exists("deals.json"):
            with open("deals.json", "r") as f:
                st.session_state["deals"] = json.load(f)
        else:
            st.session_state["deals"] = []

    st.session_state["deals"].append(st.session_state.last_result)
    with open("deals.json", "w") as f:
        json.dump(st.session_state["deals"], f, indent=2)
    st.toast("💾 Deal saved to history.", icon="💾")
