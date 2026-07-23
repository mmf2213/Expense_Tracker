import streamlit as st
import pandas as pd
import plotly.express as px
import database as db

st.set_page_config(page_title="Personal Expense Tracker", page_icon="💰", layout="wide")

# Fetch data from Supabase
df = db.fetch_expenses()

# Pre-process month-year column
if not df.empty:
    df['date'] = pd.to_datetime(df['date'])
    df['month_year'] = df['date'].dt.strftime('%Y-%m')

# ==========================================
# 1. SIDEBAR: Settings, Filters & Analytics
# ==========================================
st.sidebar.header("⚙️ Settings & Budgeting")

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

# Category Budget Limits (NEW FEATURE)
st.sidebar.subheader("🎯 Category Budgets")
categories = ["Food", "Transport", "Shopping", "Bills", "Entertainment", "Other"]

if 'category_budgets' not in st.session_state:
    st.session_state.category_budgets = {
        "Food": 3000.0,
        "Transport": 1500.0,
        "Shopping": 2000.0,
        "Bills": 2000.0,
        "Entertainment": 1000.0,
        "Other": 1000.0
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

# --- INTERACTIVE ANALYTICS IN SIDEBAR (PLOTLY) ---
st.sidebar.header("📈 Expense Analytics")

if not filtered_df.empty:
    # Category-wise Interactive Pie Chart
    st.sidebar.subheader("Category Breakdown")
    category_data = filtered_df.groupby("category")["amount"].sum().reset_index()
    fig_pie = px.pie(
        category_data, 
        values='amount', 
        names='category', 
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    fig_pie.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=250)
    st.sidebar.plotly_chart(fig_pie, use_container_width=True)

    # Monthly Spending Interactive Bar Chart
    if "month_year" in df.columns:
        st.sidebar.subheader("Monthly Spending Trend")
        monthly_data = df.groupby("month_year")["amount"].sum().reset_index()
        fig_bar = px.bar(
            monthly_data, 
            x='month_year', 
            y='amount', 
            labels={'month_year': 'Month', 'amount': 'Amount (₹)'},
            color_discrete_sequence=['#1f77b4']
        )
        fig_bar.update_layout(margin=dict(t=10, b=0, l=0, r=0), height=220)
        st.sidebar.plotly_chart(fig_bar, use_container_width=True)
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

st.title("💰 Personal Expense Tracker")

# Metrics Summary Cards
total_expense = filtered_df['amount'].sum() if not filtered_df.empty else 0.0
net_savings = monthly_income - total_expense
budget_used_pct = (total_expense / monthly_income * 100) if monthly_income > 0 else 0

col1, col2, col3 = st.columns(3)
col1.metric("Monthly Income", f"₹{monthly_income:,.2f}")
col2.metric("Total Expense", f"₹{total_expense:,.2f}")
col3.metric("Net Savings", f"₹{net_savings:,.2f}", delta=f"{100 - budget_used_pct:.1f}% remaining")

# Budget Overall Progress Bar
if monthly_income > 0:
    progress_val = min(int(budget_used_pct), 100)
    st.progress(progress_val, text=f"Overall Budget Used: {budget_used_pct:.1f}%")
    if budget_used_pct > 90:
        st.error("⚠️ Warning: You have spent over 90% of your total monthly income!")

# Category Spending Alert System (NEW FEATURE)
if not filtered_df.empty:
    cat_spent = filtered_df.groupby("category")["amount"].sum().to_dict()
    overbudget_alerts = []
    for cat, spent in cat_spent.items():
        limit = st.session_state.category_budgets.get(cat, 0.0)
        if limit > 0 and spent > limit:
            overbudget_alerts.append(f"**{cat}**: Spent ₹{spent:,.2f} / Limit ₹{limit:,.2f}")

    if overbudget_alerts:
        st.warning("🚨 **Category Budget Exceeded Alerts:**\n- " + "\n- ".join(overbudget_alerts))

st.markdown("---")

# Add New Expense Form
with st.expander("➕ Add New Expense", expanded=True):
    with st.form("expense_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            date = st.date_input("Date")
            category = st.selectbox("Category", categories)
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

# Recent Expenses Table + Delete Feature
st.subheader("📋 Recent Expenses")
if not filtered_df.empty:
    col_table, col_del = st.columns([3, 1])
    with col_del:
        if 'id' in filtered_df.columns:
            delete_id = st.selectbox("Select ID to Delete", filtered_df['id'].tolist())
            if st.button("🗑️ Delete Record"):
                db.delete_expense(delete_id)
                st.success(f"Deleted expense ID {delete_id}")
                st.rerun()

    with col_table:
        display_cols = [c for c in ['id', 'date', 'category', 'amount', 'payment_mode', 'note'] if c in filtered_df.columns]
        st.dataframe(filtered_df[display_cols], use_container_width=True)
else:
    st.info("No expenses logged yet.")
