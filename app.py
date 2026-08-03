import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
import database as db

st.set_page_config(page_title="Personal Expense & Wallet Tracker", page_icon="💰", layout="wide")

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

# Wallet Manual Balance Adjustment / Carry-Over Setup
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

# --- LAST MONTH'S SAVINGS SNAPSHOT ---
st.sidebar.header("🗓️ Previous Month Snapshot")
if not df.empty and 'month_year' in df.columns:
    # Calculate previous month string YYYY-MM
    today = datetime.date.today()
    first_day_curr_month = today.replace(day=1)
    last_month_date = first_day_curr_month - datetime.timedelta(days=1)
    last_month_str = last_month_date.strftime('%Y-%m')
    
    lm_df = df[df['month_year'] == last_month_str]
    if not lm_df.empty:
        lm_expense = lm_df[lm_df.get('type', 'EXPENSE') == 'EXPENSE']['amount'].sum() if 'type' in lm_df.columns else lm_df['amount'].sum()
        lm_income = lm_df[lm_df.get('type', 'EXPENSE') == 'INCOME']['amount'].sum() if 'type' in lm_df.columns else 0.0
        lm_savings = lm_income - lm_expense
        
        with st.sidebar.expander(f"📊 {last_month_str} Summary", expanded=False):
            st.write(f"**Total Inflow:** ₹{lm_income:,.2f}")
            st.write(f"**Total Outflow:** ₹{lm_expense:,.2f}")
            st.write(f"**Net Savings:** ₹{lm_savings:,.2f}")
    else:
        st.sidebar.caption(f"No records found for {last_month_str}.")

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

    if "month_year" in df.columns:
        st.sidebar.subheader("Monthly Spending Trend")
        m_exp = df[df.get('type', 'EXPENSE') == 'EXPENSE'] if 'type' in df.columns else df
        monthly_data = m_exp.groupby("month_year")["amount"].sum().reset_index()
        fig_bar = px.bar(
            monthly_data, x='month_year', y='amount',
            labels={'month_year': 'Month', 'amount': 'Amount (₹)'},
            color_discrete_sequence=['#1f77b4']
        )
        fig_bar.update_layout(margin=dict(t=10, b=0, l=0, r=0), height=220)
        st.sidebar.plotly_chart(fig_bar, use_container_width=True)

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
# 2. MAIN PAGE: Header, Metrics & Wallets
# ==========================================

st.title("💰 Personal Cashflow & Wallet Tracker")

# LIVE WALLET CARDS
total_net_worth = online_bal + offline_bal
w_col1, w_col2, w_col3 = st.columns(3)
w_col1.metric("💳 Online Balance (Bank/UPI)", f"₹{online_bal:,.2f}")
w_col2.metric("💵 Cash Balance (Offline)", f"₹{offline_bal:,.2f}")
w_col3.metric("🏦 Total Net Liquidity", f"₹{total_net_worth:,.2f}")

st.markdown("---")

# MONTHLY METRICS
if not filtered_df.empty and 'type' in filtered_df.columns:
    month_expenses = filtered_df[filtered_df['type'] == 'EXPENSE']['amount'].sum()
    month_extra_income = filtered_df[filtered_df['type'] == 'INCOME']['amount'].sum()
else:
    month_expenses = filtered_df['amount'].sum() if not filtered_df.empty else 0.0
    month_extra_income = 0.0

total_effective_income = monthly_income + month_extra_income
net_savings = total_effective_income - month_expenses
budget_used_pct = (month_expenses / total_effective_income * 100) if total_effective_income > 0 else 0

m_col1, m_col2, m_col3 = st.columns(3)
m_col1.metric("Effective Income", f"₹{total_effective_income:,.2f}", delta=f"+₹{month_extra_income:,.2f} logged" if month_extra_income > 0 else None)
m_col2.metric("Total Expenses", f"₹{month_expenses:,.2f}")
m_col3.metric(
    "Net Savings", 
    f"₹{net_savings:,.2f}", 
    delta=f"{100 - budget_used_pct:.1f}% remaining",
    delta_color="normal" if net_savings >= 0 else "inverse"
)

# Budget Overall Progress Bar
if total_effective_income > 0:
    progress_val = min(int(budget_used_pct), 100)
    st.progress(progress_val, text=f"Overall Budget Used: {budget_used_pct:.1f}%")
    if budget_used_pct > 90:
        st.error("⚠️ Warning: You have spent over 90% of your available funds!")

# Category Spending Alerts
if not filtered_df.empty:
    exp_df = filtered_df[filtered_df.get('type', 'EXPENSE') == 'EXPENSE'] if 'type' in filtered_df.columns else filtered_df
    cat_spent = exp_df.groupby("category")["amount"].sum().to_dict()
    overbudget_alerts = []
    for cat, spent in cat_spent.items():
        limit = st.session_state.category_budgets.get(cat, 0.0)
        if limit > 0 and spent > limit:
            overbudget_alerts.append(f"**{cat}**: Spent ₹{spent:,.2f} / Limit ₹{limit:,.2f}")

    if overbudget_alerts:
        st.warning("🚨 **Category Budget Exceeded Alerts:**\n- " + "\n- ".join(overbudget_alerts))

st.markdown("---")

# ==========================================
# 3. TRANSACTION FORMS & ATM TRANSFER
# ==========================================

action_tab1, action_tab2, action_tab3 = st.tabs(["🔴 Log Expense", "🟢 Log Income / Credit", "🏧 ATM / Wallet Transfer"])

# TAB 1: LOG EXPENSE
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
            st.success("Expense recorded and wallet balance updated!")
            st.rerun()

# TAB 2: LOG INCOME
with action_tab2:
    with st.form("income_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            date = st.date_input("Date", datetime.date.today(), key="inc_date")
            inc_category = st.selectbox("Source", ["Family / Allowance", "Scholarship / Govt Scheme", "Salary / Stipend", "Gift / Other"], key="inc_cat")
            amount = st.number_input("Amount Received (₹)", min_value=0.01, step=100.0, key="inc_amt")
        with col2:
            payment_mode = st.selectbox("Received In", ["UPI", "Debit Card", "Cash"], key="inc_mode")
            note = st.text_input("Note (e.g., Ladki Bahin, Mom)", key="inc_note")
        
        submitted = st.form_submit_button("Record Income")
        if submitted:
            db.add_transaction(date, inc_category, amount, payment_mode, note, trans_type="INCOME")
            st.success("Income recorded and wallet balance updated!")
            st.rerun()

# TAB 3: ATM / INTER-WALLET TRANSFER
with action_tab3:
    st.caption("Move money between digital bank balance and physical cash (e.g., ATM withdrawal).")
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
# 4. RECENT TRANSACTIONS LEDGER TABLE
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
            
        # Format transaction type with emojis
        if 'type' in table_df.columns:
            table_df['type'] = table_df['type'].apply(lambda x: "🟢 INCOME" if x == "INCOME" else "🔴 EXPENSE")
            
        st.dataframe(table_df, use_container_width=True)
else:
    st.info("No transactions logged for this period.")
