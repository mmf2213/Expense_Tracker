import datetime
import streamlit as st
import pandas as pd
import database as db

st.set_page_config(page_title="Expense Tracker", page_icon="💰", layout="wide")

st.title("💰 Expense & Wallet Tracker")

# Sidebar: Wallet Overview & Transfers
st.sidebar.header("💳 Wallets")
wallets = db.get_wallets()
online_bal = float(wallets.get('online_balance', 0.0))
offline_bal = float(wallets.get('offline_balance', 0.0))

st.sidebar.metric("Online Balance", f"₹{online_bal:,.2f}")
st.sidebar.metric("Cash Balance", f"₹{offline_bal:,.2f}")
st.sidebar.metric("Total Liquidity", f"₹{(online_bal + offline_bal):,.2f}")

st.sidebar.divider()
st.sidebar.subheader("🔄 Transfer Funds")
transfer_amt = st.sidebar.number_input("Amount", min_value=1.0, step=10.0, key="trans_amt")
direction = st.sidebar.selectbox("Direction", ["ONLINE_TO_CASH", "CASH_TO_ONLINE"])

if st.sidebar.button("Transfer"):
    success, msg = db.transfer_funds(transfer_amt, direction)
    if success:
        st.sidebar.success(msg)
        st.rerun()
    else:
        st.sidebar.error(msg)

# Main Form: Add Transaction
st.subheader("➕ Add New Entry")
col1, col2, col3 = st.columns(3)

with col1:
    trans_date = st.date_input("Date", datetime.date.today())
    trans_type = st.selectbox("Type", ["EXPENSE", "INCOME"])
with col2:
    category = st.text_input("Category", placeholder="Food, Travel, Salary, etc.")
    amount = st.number_input("Amount (₹)", min_value=0.01, step=10.0)
with col3:
    payment_mode = st.selectbox("Payment Mode", ["UPI", "Debit Card", "Cash", "Online"])
    note = st.text_input("Note", placeholder="Optional description")

if st.button("Save Transaction", type="primary"):
    if not category:
        st.warning("Please specify a category.")
    else:
        res = db.add_transaction(
            date=trans_date,
            category=category,
            amount=amount,
            payment_mode=payment_mode,
            note=note,
            trans_type=trans_type
        )
        if res:
            st.success("Transaction saved!")
            st.rerun()

st.divider()

# Ledger Table
st.subheader("📋 Ledger History")
records = db.fetch_expenses()

if records:
    df = pd.DataFrame(records)
    cols = [c for c in ['id', 'date', 'type', 'category', 'amount', 'payment_mode', 'note'] if c in df.columns]
    st.dataframe(df[cols], use_container_width=True)

    # Delete Row Section
    st.subheader("🗑️ Delete Record")
    del_id = st.number_input("Enter Transaction ID to delete", min_value=1, step=1)
    if st.button("Delete"):
        db.delete_expense(del_id)
        st.success(f"Deleted transaction #{del_id}")
        st.rerun()
else:
    st.info("No transactions recorded yet.")
