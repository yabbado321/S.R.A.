# mobile_app.py - Mobile version of Smart Rental Analyzer
import streamlit as st
import numpy as np
import numpy_financial as npf
import os, json

st.set_page_config(page_title="📱 Rental Analyzer (Mobile)", layout="centered")
st.title("📱 Smart Rental Analyzer (Mobile)")
st.caption("Quick analysis tool optimized for mobile users.")
st.markdown("For Full Features Use Desktop Mode")

# ─────────────────────────── Session Setup ───────────────────────────
if "deals" not in st.session_state:
    if os.path.exists("deals.json"):
        with open("deals.json", "r") as f:
            st.session_state["deals"] = json.load(f)
    else:
        st.session_state["deals"] = []


# ─────────────────────────── Quick Deal Analyzer ───────────────────────────
st.title("📊 Quick Deal Analyzer (Mobile)")
st.caption("Estimate ROI, Cap Rate, Cash Flow & Score on the go")

with st.form("quick_deal_form"):
    name = st.text_input("🏠 Property Name", value="Untitled Deal")
    price = st.number_input("Purchase Price ($)", min_value=0.0, value=250000.0)
    rent = st.number_input("Monthly Rent ($)", min_value=0.0, value=2200.0)
    expenses = st.number_input("Monthly Expenses ($)", min_value=0.0, value=1400.0)
    down_pct = st.slider("Down Payment (%)", 0.0, 100.0, value=20.0, step=1.0)
    deal_type = st.selectbox("Deal Type", ["Buy & Hold", "BRRRR", "Fix & Flip", "Other"])
    notes = st.text_area("Notes or Strategy", placeholder="E.g. Fix & Flip, Buy & Hold")
    submitted = st.form_submit_button("🔍 Analyze Deal")

if submitted:
    down_payment = price * down_pct / 100
    annual_cf = (rent - expenses) * 12
    roi = (annual_cf / down_payment) * 100 if down_payment else 0
    cap_rate = ((rent - expenses) * 12 / price) * 100 if price else 0

    score = min(roi, 20)/20*60 + min(cap_rate, 10)/10*30 + (10 if annual_cf > 0 else -10)
    score = max(0, min(score, 100))

    st.metric("ROI", f"{roi:.1f}%")
    st.metric("Cap Rate", f"{cap_rate:.1f}%")
    st.metric("Annual Cash Flow", f"${annual_cf:,.0f}")
    st.metric("Score", f"{score:.1f}/100")

    result = {
        "title": name,
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
        "status": "📱 Mobile Entry"
    }

    st.session_state["deals"].append(result)
    with open("deals.json", "w") as f:
        json.dump(st.session_state["deals"], f, indent=2)

    st.success("✅ Deal saved!")

# ─────────────────────────── Break-Even Calculator ───────────────────────────
st.markdown("---")
st.header("💡 Break-Even Calculator")

price = st.number_input("Property Price ($)", 0.0, 1e9, 250000.0)
down_pct = st.slider("Down Payment (%)", 0.0, 100.0, 20.0)
interest_rate = st.number_input("Interest Rate (%)", 0.0, 20.0, 6.5)
term = st.selectbox("Loan Term (Years)", [15, 30], index=1)
taxes_insurance = st.number_input("Taxes + Insurance + HOA ($/mo)", 0.0, 5000.0, 300.0)
vacancy = st.slider("Vacancy Rate (%)", 0.0, 30.0, 5.0)
mgmt = st.slider("Management Fee (% of Rent)", 0.0, 20.0, 8.0)
maint = st.slider("Maintenance (% of Rent)", 0.0, 20.0, 10.0)

loan = price * (1 - down_pct / 100)
m_int = interest_rate / 100 / 12
months = term * 12
mortgage = npf.pmt(m_int, months, -loan) if loan > 0 else 0

# Estimate break-even rent
for r in range(500, 5000, 10):
    vac_loss = r * vacancy / 100
    mgmt_cost = r * mgmt / 100
    maint_cost = r * maint / 100
    total_exp = taxes_insurance + vac_loss + mgmt_cost + maint_cost + mortgage
    if r >= total_exp:
        st.success(f"📌 Estimated Break-Even Rent: ${r:,.0f}/mo")
        break
else:
    st.error("❌ Could not determine break-even rent in tested range.")

# ─────────────────────────── Multi-Year ROI & IRR ───────────────────────────
st.markdown("---")
st.header("📘 Multi-Year ROI + IRR")

years = st.slider("Years to Project", 1, 30, 5)
appreciation = st.slider("Annual Appreciation (%)", 0.0, 10.0, 3.0)
rent_growth = st.slider("Rent Growth (%/yr)", 0.0, 10.0, 2.5)
exp_growth = st.slider("Expense Growth (%/yr)", 0.0, 10.0, 2.0)

r = rent
e = expenses
v = price
b = loan
dp = price * down_pct / 100
m = mortgage

roi_list = []
cf_list = []
eq_list = []
cash_flows = [-dp]

for y in range(1, years + 1):
    cf = (r - e - m) * 12
    for _ in range(12):
        interest = b * m_int
        principal = m - interest
        b -= principal

    v *= 1 + appreciation / 100
    equity = v - b
    roi = ((cf + (equity - dp)) / dp) * 100 if dp else 0

    roi_list.append(roi)
    cf_list.append(cf)
    eq_list.append(equity)
    cash_flows.append(cf)

sale_value = v
selling_cost = 0.06 * sale_value
net_sale = sale_value - selling_cost - b
cash_flows[-1] += net_sale

irr = npf.irr(cash_flows) * 100 if len(cash_flows) > 1 else 0

st.metric("Final ROI", f"{roi_list[-1]:.1f}%")
st.metric("Estimated IRR", f"{irr:.1f}%")

# ─────────────────────────── Deal History ───────────────────────────
st.markdown("---")
st.header("📂 Deal History")

if st.session_state["deals"]:
    for deal in reversed(st.session_state["deals"][-5:]):
        with st.expander(f"🏠 {deal['title']} ({deal['type']})"):
            st.write(f"**ROI**: {deal['roi']}%")
            st.write(f"**Cap Rate**: {deal['cap']}%")
            st.write(f"**Cash Flow**: ${float(deal['cf']):,.0f}")
            st.write(f"**Score**: {deal['score']}/100")
            if deal.get("notes"):
                st.write(f"**Notes**: {deal['notes']}")
else:
    st.info("No deals saved yet. Analyze one above!")
