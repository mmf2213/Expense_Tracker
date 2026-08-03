import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
import json
import os
from google import genai
from google.genai import types
import database as db

st.set_page_config(page_title="Personal Expense & Wallet Tracker", page_icon="💰", layout="wide")

# Initialize Gemini Client
gemini_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY", "")
ai_client = genai.Client(api_key=gemini_key) if gemini_key else None

# Fetch data from Supabase
raw_data = db.fetch_expenses()
df = pd.DataFrame(raw_data) if raw_data else pd.DataFrame()

# Pre-process month-year column
if not df.empty:
    df['date'] = pd.to_datetime(df['date'])
    df['month_year'] = df['date'].dt.strftime('%Y-%m')

# Fetch Live Wallets
wallets = db.get_wallets()
online_bal = float(wallets.get('online_balance', 0.0))
offline_bal = float(wallets.get('offline_balance', 0.0))

# Get Current Month
current_month_str = datetime.datetime.now().strftime('%Y-%m')

# ==========================================
# 1. SIDEBAR: Settings, Wallets & Analytics
# ==========================================
st.sidebar.header("⚙️ Wallet & Budget Settings")

# Wallet Manual Balance Adjustment
with st.sidebar.expander("💳 Adjust / Set Wallet Balances", expanded=False):
    st.caption("Set or manually adjust starting balances.")
    new_online = st.number_input("Online Balance (₹)", min_value=0.0, value=online_bal, step=100.0)
    new_offline = st.number_input("Cash Balance (₹)", min_value=0.0, value=offline_bal, step=100.0)
    if st.button("Save Wallet Balances"):
        db.update_wallets(new_online, new_offline)
        st.success("Wallet balances updated!")
        st.rerun()

# Income Setting
if 'monthly_income' not in st.session_state:
    st.session_state.monthly_income = 10000.00

monthly_income = st.sidebar.number_input(
    "Base Expected Income (₹)",
    min_value=0.0,
    value=st.session_state.monthly_income,
    step=500.0,
    key="income_input"
)
st.session_state.monthly_income = monthly_income

# Category Budget Limits
st.sidebar.subheader("🎯 Category Expense Budgets")
categories = ["Food", "Rent", "Transport", "Shopping", "Bills"]

if 'category_budgets' not in st.session_state:
    st.session_state.category_budgets = {
        "Rent": 4500.0,
        "Food": 3000.0,
        "Transport": 500.0,
        "Shopping": 1000.0,
        "Bills": 1000.0
    }

with st.sidebar.expander("Set Category Limits (₹)"):
    for cat in categories:
        st.session_state.category_budgets[cat] = st.number_input(
            f"{cat} Limit",
            min_value=0.0,
            value=st.session_state.category_budgets.get(cat, 1000.0),
            step=100.0,
            key=f"budget_{cat}"
        )

# Filter View Logic
selected_month = current_month_str
if not df.empty:
    available_months = sorted(df['month_year'].unique().tolist(), reverse=True)
    if current_month_str not in available_months:
        available_months.insert(0, current_month_str)
    
    options = [f"Current Month ({current_month_str})", "All"] + [m for m in available_months if m != current_month_str]
    selected_option = st.sidebar.selectbox("Filter View", options, index=0)
    
    if selected_option == f"Current Month ({current_month_str})":
        filtered_df = df[df['month_year'] == current_month_str] if 'month_year' in df.columns else df
        selected_month = current_month_str
    elif selected_option == "All":
        filtered_df = df.copy()
        selected_month = "All"
    else:
        selected_month = selected_option
        filtered_df = df[df['month_year'] == selected_month] if 'month_year' in df.columns else df
else:
    filtered_df = df.copy()

st.sidebar.markdown("---")

# Analytics Plotly Charts
st.sidebar.header("📈 Expense Analytics")
if not filtered_df.empty:
    expense_only = filtered_df[filtered_df.get('type', 'EXPENSE') == 'EXPENSE'] if 'type' in filtered_df.columns else filtered_df
    
    if not expense_only.empty:
        st.sidebar.subheader("Category Breakdown")
        category_data = expense_only.groupby("category")["amount"].sum().reset_index()
        fig_pie = px.pie(
            category_data, values='amount', names='category', hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig_pie.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=230)
        st.sidebar.plotly_chart(fig_pie, use_container_width=True)

# Export Data Button
if not df.empty:
    st.sidebar.markdown("---")
    st.sidebar.download_button(
        label="📥 Export Ledger to CSV",
        data=df.to_csv(index=False),
        file_name="financial_ledger.csv",
        mime="text/csv"
    )

# ==========================================
# 2. MAIN PAGE: Header & Metrics
# ==========================================

st.title("💰 Personal Cashflow & Wallet Tracker")

# LIVE WALLET CARDS
total_net_worth = online_bal + offline_bal
w_col1, w_col2, w_col3 = st.columns(3)
w_col1.metric("💳 Online Balance (Bank/UPI)", f"₹{online_bal:,.2f}")
w_col2.metric("💵 Cash Balance (Offline)", f"₹{offline_bal:,.2f}")
w_col3.metric("🏦 Total Net Liquidity", f"₹{total_net_worth:,.2f}")

st.markdown("---")

# ==========================================
# 3. AI QUICK INPUT SECTION
# ==========================================

st.subheader("🤖 AI Smart Quick-Input")
st.caption("Type in natural language e.g. *'Spent 150 on dinner via UPI'*, *'Got 2000 cash from mom'*, or *'Withdrew 1000 from ATM'*")

ai_prompt = st.text_input("Enter transaction:", placeholder="e.g. Spent 200 on snacks using Google Pay")

if st.button("✨ Auto-Process with AI"):
    if not ai_client:
        st.error("Gemini API Key is missing. Please set GEMINI_API_KEY in Streamlit Secrets.")
    elif not ai_prompt.strip():
        st.warning("Please enter a transaction statement first.")
    else:
        system_instruction = """
        You are an assistant parsing financial transactions into JSON.
        Output MUST be strict JSON with these keys:
        - action_type: "TRANSACTION" or "TRANSFER"
        - trans_type: "EXPENSE" or "INCOME" (if action_type is TRANSACTION)
        - amount: float number
        - category: one of ["Food", "Rent", "Transport", "Shopping", "Bills", "Allowance", "Scholarship", "Other"]
        - payment_mode: "UPI" or "Cash" or "Debit Card"
        - direction: "ONLINE_TO_CASH" or "CASH_TO_ONLINE" (if action_type is TRANSFER)
        - note: brief description string
        """
        try:
            response = ai_client.models.generate_content(
                model="gemini-1.5-flash",
                contents=ai_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json"
                )
            )
            parsed = json.loads(response.text)
            
            if parsed.get("action_type") == "TRANSFER":
                amt = float(parsed.get("amount", 0.0))
                dir_code = parsed.get("direction", "ONLINE_TO_CASH")
                success, msg = db.transfer_funds(amt, dir_code)
                if success:
                    st.success(f"🤖 AI Action Executed: {msg}")
                    st.rerun()
                else:
                    st.error(msg)
            else:
                db.add_transaction(
                    date=datetime.date.today(),
                    category=parsed.get("category", "Other"),
                    amount=float(parsed.get("amount", 0.0)),
                    payment_mode=parsed.get("payment_mode", "UPI"),
                    note=parsed.get("note", ai_prompt),
                    trans_type=parsed.get("trans_type", "EXPENSE")
                )
                st.success(f"🤖 AI Action Executed: Recorded {parsed.get('trans_type')} of ₹{parsed.get('amount')} under {parsed.get('category')}!")
                st.rerun()
        except Exception as e:
            st.error(f"Failed to process prompt: {str(e)}")

st.markdown("---")

# ==========================================
# 4. MANUAL TRANSACTION FORMS & ATM TRANSFER
# ==========================================

action_tab1, action_tab2, action_tab3 = st.tabs(["🔴 Log Expense", "🟢 Log Income / Credit", "🏧 ATM / Wallet Transfer"])

with action_tab1:
    with st.form("expense_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            date = st.date_input("Date", datetime.date.today(), key="exp_date")
            category = st.selectbox("Category", categories, key="exp_cat")
            amount = st.number_input("Amount (₹)", min_value=0.01, step=10.0, key="exp_amt")
        with col2:
            payment_mode = st.selectbox("Payment Mode", ["UPI", "Debit Card", "Cash"], key="exp_mode")
            note = st.text_input("Note (Optional)", key="exp_note")
        
        submitted = st.form_submit_button("Record Expense")
        if submitted:
            db.add_transaction(date, category, amount, payment_mode, note, trans_type="EXPENSE")
            st.success("Expense recorded!")
            st.rerun()

with action_tab2:
    with st.form("income_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            date = st.date_input("Date", datetime.date.today(), key="inc_date")
            inc_category = st.selectbox("Source", ["Family / Allowance", "Scholarship / Govt Scheme", "Salary / Stipend", "Gift / Other"], key="inc_cat")
            amount = st.number_input("Amount Received (₹)", min_value=0.01, step=100.0, key="inc_amt")
        with col2:
            payment_mode = st.selectbox("Received In", ["UPI", "Debit Card", "Cash"], key="inc_mode")
            note = st.text_input("Note", key="inc_note")
        
        submitted = st.form_submit_button("Record Income")
        if submitted:
            db.add_transaction(date, inc_category, amount, payment_mode, note, trans_type="INCOME")
            st.success("Income recorded!")
            st.rerun()

with action_tab3:
    st.caption("Move money between digital bank balance and physical cash (ATM Withdrawal/Deposit).")
    col1, col2, col3 = st.columns(3)
    with col1:
        transfer_dir = st.selectbox("Direction", ["Online to Cash (ATM Withdrawal)", "Cash to Online (Cash Deposit)"])
    with col2:
        transfer_amt = st.number_input("Transfer Amount (₹)", min_value=1.0, step=100.0)
    with col3:
        st.write(" ")
        st.write(" ")
        if st.button("Execute Transfer"):
            direction_code = "ONLINE_TO_CASH" if "Online to Cash" in transfer_dir else "CASH_TO_ONLINE"
            success, msg = db.transfer_funds(transfer_amt, direction_code)
            if success:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

st.markdown("---")

# ==========================================
# 5. RECENT TRANSACTIONS LEDGER TABLE
# ==========================================

st.subheader("📋 Transaction Ledger")
if not filtered_df.empty:
    col_table, col_del = st.columns([3, 1])
    with col_del:
        if 'id' in filtered_df.columns:
            delete_id = st.selectbox("Select ID to Delete", filtered_df['id'].tolist())
            if st.button("🗑️ Delete Record"):
                db.delete_expense(delete_id)
                st.success(f"Deleted record ID {delete_id}")
                st.rerun()

    with col_table:
        display_cols = [c for c in ['id', 'type', 'date', 'category', 'amount', 'payment_mode', 'note'] if c in filtered_df.columns]
        table_df = filtered_df[display_cols].copy()
        if 'date' in table_df.columns:
            table_df['date'] = table_df['date'].dt.strftime('%Y-%m-%d')
            
        if 'type' in table_df.columns:
            table_df['type'] = table_df['type'].apply(lambda x: "🟢 INCOME" if x == "INCOME" else "🔴 EXPENSE")
            
        st.dataframe(table_df, use_container_width=True)
else:
    st.info("No transactions logged for this period.")
