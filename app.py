import streamlit as st
import pandas as pd
import database as db

st.set_page_config(page_title="Personal Expense Tracker", page_icon="💰", layout="wide")

# Fetch data from Supabase
df = db.fetch_expenses()

# ==========================================
# 1. SIDEBAR: Settings, Filters & Analytics
# ==========================================
st.sidebar.header("⚙️ Settings & Filters")

# Income Setting
if 'monthly_income' not in st.session_state:
    st.session_state.monthly_income = 10000.00

monthly_income = st.sidebar.number_input(
    "Enter Monthly Income (₹)",
    min_value=0.0,
    value=st.session_state.monthly_income,
    step=500.0,
    key="income_input"
)
st.session_state.monthly_income = monthly_income

# Month Filter
selected_month = "All"
if not df.empty:
    df['month_year'] = df['date'].dt.strftime('%Y-%m')
    months = ["All"] + sorted(df['month_year'].unique().tolist(), reverse=True)
    selected_month = st.sidebar.selectbox("Filter by Month", months)

# Export Data Button in Sidebar
if not df.empty:
    st.sidebar.markdown("---")
    st.sidebar.download_button(
        label="📥 Export Expenses to CSV",
        data=df.to_csv(index=False),
        file_name="expenses.csv",
        mime="text/csv"
    )

# ==========================================
# 2. MAIN PAGE: Quick Add & Overview
# ==========================================
st.title("💰 Personal Expense Tracker")

# --- Quick Add Form (First thing visible on Mobile) ---
with st.expander("➕ Add New Expense", expanded=True):
    with st.form("expense_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            date = st.date_input("Date")
            category = st.selectbox("Category", ["Food", "Transport", "Shopping", "Bills", "Entertainment", "Other"])
            amount = st.number_input("Amount (₹)", min_value=0.01, step=10.0)
        with col2:
            payment_mode = st.selectbox("Payment Mode", ["Cash", "UPI", "Debit Card"])
            note = st.text_input("Note (Optional)")
        
        submitted = st.form_submit_button("Add Expense")
        if submitted:
            db.add_expense(date, category, amount, payment_mode, note)
            st.success("Expense added successfully!")
            st.rerun()

st.markdown("---")

# --- Filter Data ---
filtered_df = df.copy()
if not filtered_df.empty and selected_month != "All":
    filtered_df = filtered_df[filtered_df['month_year'] == selected_month]

# --- Metrics Cards ---
total_expense = filtered_df['amount'].sum() if not filtered_df.empty else 0.0
net_savings = monthly_income - total_expense

col1, col2, col3 = st.columns(3)
col1.metric("Monthly Income", f"₹{monthly_income:,.2f}")
col2.metric("Total Expense", f"₹{total_expense:,.2f}")
col3.metric("Net Savings", f"₹{net_savings:,.2f}", delta=f"{net_savings:,.2f}")

st.markdown("---")

# --- Recent Transactions Table ---
st.subheader("📋 Recent Expenses")
if not filtered_df.empty:
    st.dataframe(filtered_df[['date', 'category', 'amount', 'payment_mode', 'note']], use_container_width=True)
else:
    st.info("No expenses logged yet.")
