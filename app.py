import datetime
import streamlit as st
import pandas as pd
import database as db

st.set_page_config(page_title="Expense Tracker", page_icon="💰", layout="wide")

st.title("💰 Personal Expense & Wallet Manager")

# ==========================================
# SIDEBAR - WALLETS, STARTING BALANCES & ATM
# ==========================================
st.sidebar.header("💳 Wallet Balances")
wallets = db.get_wallets()
online_bal = float(wallets.get('online_balance', 0.0))
offline_bal = float(wallets.get('offline_balance', 0.0))

st.sidebar.metric("Online Balance", f"₹{online_bal:,.2f}")
st.sidebar.metric("Cash Balance", f"₹{offline_bal:,.2f}")
st.sidebar.metric("Total Liquidity", f"₹{(online_bal + offline_bal):,.2f}")

st.sidebar.divider()

# ⚙️ SET START-OF-MONTH BALANCES
with st.sidebar.expander("⚙️ Set Month Starting Balances"):
    default_online = max(0.0, online_bal)
    default_cash = max(0.0, offline_bal)

    new_online = st.number_input("Starting Online Balance (₹)", value=default_online, step=100.0)
    new_cash = st.number_input("Starting Cash Balance (₹)", value=default_cash, step=100.0)
    
    if st.button("Set Initial Balances", type="primary"):
        res = db.set_starting_balances(new_online, new_cash)
        if res:
            st.success("Starting balances updated!")
            st.rerun()

st.sidebar.divider()

# 🏧 ATM TRANSFER / DEPOSIT
st.sidebar.subheader("🏧 ATM Transfer / Deposit")
transfer_amt = st.sidebar.number_input("Transfer Amount (₹)", min_value=1.0, step=10.0, key="trans_amt")
direction = st.sidebar.selectbox(
    "Transfer Direction", 
    ["ONLINE_TO_CASH", "CASH_TO_ONLINE"],
    format_func=lambda x: "ATM Withdrawal (Online ➔ Cash)" if x == "ONLINE_TO_CASH" else "Cash Deposit (Cash ➔ Online)"
)

if st.sidebar.button("Execute Transfer"):
    success, msg = db.transfer_funds(transfer_amt, direction)
    if success:
        st.sidebar.success(msg)
        st.rerun()
    else:
        st.sidebar.error(msg)

# ==========================================
# MAIN PAGE - ADD INCOME OR EXPENSE
# ==========================================
st.subheader("➕ Add New Entry")

CATEGORIES = [
    "Food & Snacks", 
    "Groceries & Dmart", 
    "Bills & Recharge", 
    "Travel & Auto", 
    "Shopping", 
    "Salary / Income", 
    "Entertainment", 
    "Health & Medical", 
    "Other"
]

col1, col2, col3 = st.columns(3)

with col1:
    trans_date = st.date_input("Date", datetime.date.today())
    trans_type = st.selectbox("Transaction Type", ["EXPENSE", "INCOME"])

with col2:
    category = st.selectbox("Category", CATEGORIES)
    amount = st.number_input("Amount (₹)", min_value=0.01, step=10.0)

with col3:
    payment_mode = st.selectbox("Payment Mode", ["UPI", "Debit Card", "Cash", "Online"])
    note = st.text_input("Note", placeholder="e.g., Lunch, Recharge, Dmart, etc.")

if st.button("Save Entry", type="primary"):
    res = db.add_transaction(
        date=trans_date,
        category=category,
        amount=amount,
        payment_mode=payment_mode,
        note=note,
        trans_type=trans_type
    )
    if res:
        st.success(f"Recorded {trans_type.lower()} of ₹{amount:,.2f}!")
        st.rerun()

st.divider()

# ==========================================
# TRANSACTIONS LEDGER & DELETION
# ==========================================
st.subheader("📋 Ledger History")

records = db.fetch_expenses()

if records:
    df = pd.DataFrame(records)
    
    # Filter columns cleanly
    display_cols = [c for c in ['id', 'date', 'type', 'category', 'amount', 'payment_mode', 'note'] if c in df.columns]
    st.dataframe(df[display_cols], use_container_width=True)

    # Delete Action
    st.subheader("🗑️ Delete Entry")
    del_id = st.number_input("Enter ID to delete", min_value=1, step=1)
    if st.button("Delete Row"):
        db.delete_expense(del_id)
        st.success(f"Deleted transaction #{del_id}")
        st.rerun()
else:
    st.info("No records logged yet.")
