import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import database as db

st.set_page_config(page_title="Personal Expense Tracker", page_icon="💰", layout="wide")

# Fetch data from Supabase
df = db.fetch_expenses()

# Pre-process month-year column
if not df.empty:
    df['month_year'] = df['date'].dt.strftime('%Y-%m')

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
    months = ["All"] + sorted(df['month_year'].unique().tolist(), reverse=True)
    selected_month = st.sidebar.selectbox("Filter by Month", months)

# Filter Data based on selection
filtered_df = df.copy()
if not filtered_df.empty and selected_month != "All":
    filtered_df = filtered_df[filtered_df['month_year'] == selected_month]

st.sidebar.markdown("---")

# --- EXPENSE ANALYTICS IN SIDEBAR ---
st.sidebar.header("📈 Expense Analytics")

if not filtered_df.empty:
    # Category-wise Pie Chart
    st.sidebar.subheader("Category Breakdown")
    category_data = filtered_df.groupby("category")["amount"].sum()
    
    fig, ax = plt.subplots(figsize=(4, 4))
    ax.pie(
        category_data, 
        labels=category_data.index, 
        autopct="%1.1f%%", 
        startangle=90
    )
    ax.axis("equal")
    st.sidebar.pyplot(fig)

    # Monthly Spending Bar Chart
    if "month_year" in df.columns:
        st.sidebar.subheader("Monthly Spending Trend")
        monthly_data = df.groupby("month_year")["amount"].sum()
        
        fig2, ax2 = plt.subplots(figsize=(4, 3))
        ax2.bar(monthly_data.index, monthly_data.values, color="#1f77b4")
        ax2.set_xlabel("Month")
        ax2.set_ylabel("Amount (₹)")
        plt.xticks(rotation=45)
        st.sidebar.pyplot(fig2)
else:
    st.sidebar.info("No expense data available for charts.")

# Export Data Button
if not df.empty:
    st.sidebar.markdown("---")
    st.sidebar.download_button(
        label="📥 Export Expenses to CSV",
        data=df.to_csv(index=False),
        file_name="expenses.csv",
        mime="text/csv"
    )

# ==========================================
# 2. MAIN PAGE: Add Expense, Metrics & Table
# ==========================================

# Metrics Summary Cards
total_expense = filtered_df['amount'].sum() if not filtered_df.empty else 0.0
net_savings = monthly_income - total_expense

col1, col2, col3 = st.columns(3)
col1.metric("Monthly Income", f"₹{monthly_income:,.2f}")
col2.metric("Total Expense", f"₹{total_expense:,.2f}")
col3.metric("Net Savings", f"₹{net_savings:,.2f}")

st.markdown("---")

st.title("💰 Personal Expense Tracker")

# Add New Expense Form
with st.expander("➕ Add New Expense", expanded=True):
    with st.form("expense_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            date = st.date_input("Date")
            category = st.selectbox("Category", ["Food", "Transport", "Shopping", "Bills", "Entertainment", "Other"])
            amount = st.number_input("Amount (₹)", min_value=0.01, step=10.0)
        with col2:
            payment_mode = st.selectbox("Payment Mode", ["Cash", "UPI", "Credit Card", "Debit Card", "Net Banking"])
            note = st.text_input("Note (Optional)")
        
        submitted = st.form_submit_button("Add Expense")
        if submitted:
            db.add_expense(date, category, amount, payment_mode, note)
            st.success("Expense added successfully!")
            st.rerun()

st.markdown("---")

# Metrics Summary Cards
total_expense = filtered_df['amount'].sum() if not filtered_df.empty else 0.0
net_savings = monthly_income - total_expense

col1, col2, col3 = st.columns(3)
col1.metric("Monthly Income", f"₹{monthly_income:,.2f}")
col2.metric("Total Expense", f"₹{total_expense:,.2f}")
col3.metric("Net Savings", f"₹{net_savings:,.2f}")

st.markdown("---")

# Recent Expenses Table
st.subheader("📋 Recent Expenses")
if not filtered_df.empty:
    st.dataframe(filtered_df[['date', 'category', 'amount', 'payment_mode', 'note']], use_container_width=True)
else:
    st.info("No expenses logged yet.")
