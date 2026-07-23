import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
import datetime

import database as db

# Page Setup
st.set_page_config(page_title="Personal Expense Tracker", page_icon="💰", layout="wide")
st.title("💰 Personal Expense Tracker")

# Initialize database
db.init_db()

# Categories & Payment Modes Options
CATEGORIES = ["Food", "Shopping", "Fuel", "Rent", "Bills", "Others"]
PAYMENT_MODES = ["Cash", "UPI", "Credit Card", "Debit Card", "Net Banking"]

# Sidebar: Monthly Income Input & Add Expense Form
st.sidebar.header("📊 Income Settings")
monthly_income = st.sidebar.number_input("Enter Monthly Income (₹)", min_value=0.0, value=50000.0, step=1000.0)

st.sidebar.markdown("---")
st.sidebar.header("➕ Add New Expense")

with st.sidebar.form("expense_form", clear_on_submit=True):
    expense_date = st.date_input("Date", datetime.date.today())
    category = st.selectbox("Category", CATEGORIES)
    amount = st.number_input("Amount (₹)", min_value=0.01, step=10.0)
    payment_mode = st.selectbox("Payment Mode", PAYMENT_MODES)
    note = st.text_input("Note (Optional)")
    
    submitted = st.form_submit_button("Add Expense")
    if submitted:
        db.add_expense(expense_date, category, amount, payment_mode, note)
        st.sidebar.success("Expense added successfully!")
        st.rerun()

# Load Data
df = db.fetch_expenses()

if df.empty:
    st.info("No expense records found. Add your first expense using the sidebar!")
else:
    # Filter Section
    st.subheader("🔍 Filters & View")
    
    # Extract Month-Year for Filtering
    df['YearMonth'] = df['date'].dt.strftime('%Y-%m')
    available_months = sorted(df['YearMonth'].unique(), reverse=True)
    
    selected_month = st.selectbox("Filter by Month", available_months)
    
    # Filtered DataFrame
    filtered_df = df[df['YearMonth'] == selected_month].copy()
    
    # Summary Metrics
    st.markdown("---")
    total_expense = filtered_df['amount'].sum()
    net_savings = monthly_income - total_expense
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Monthly Income", f"₹{monthly_income:,.2f}")
    col2.metric("Total Monthly Expense", f"₹{total_expense:,.2f}")
    col3.metric("Net Balance / Savings", f"₹{net_savings:,.2f}", delta_color="normal")
    
    st.markdown("---")
    
    # Charts Section
    st.subheader("📈 Expense Analytics")
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.write("### Category-wise Expenses")
        if not filtered_df.empty:
            cat_data = filtered_df.groupby('category')['amount'].sum()
            fig1, ax1 = plt.subplots(figsize=(6, 6))
            ax1.pie(cat_data, labels=cat_data.index, autopct='%1.1f%%', startangle=90)
            ax1.axis('equal')
            st.pyplot(fig1)
        else:
            st.write("No data available for selected month.")
            
    with col_chart2:
        st.write("### Monthly Spending Graph")
        if not filtered_df.empty:
            daily_data = filtered_df.groupby(filtered_df['date'].dt.strftime('%d-%b'))['amount'].sum()
            fig2, ax2 = plt.subplots(figsize=(6, 4))
            daily_data.plot(kind='bar', ax=ax2)
            ax2.set_ylabel("Amount (₹)")
            ax2.set_xlabel("Date")
            plt.xticks(rotation=45)
            st.pyplot(fig2)
        else:
            st.write("No data available for selected month.")

    st.markdown("---")
    
    # Data Table & Operations Section
    col_table, col_actions = st.columns([3, 1])
    
    with col_table:
        st.subheader("📋 Expense Log")
        display_df = filtered_df.drop(columns=['YearMonth']).copy()
        display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
        st.dataframe(display_df, use_container_width=True)
        
    with col_actions:
        st.subheader("⚙️ Actions")
        
        # Delete Expense Option
        expense_to_delete = st.selectbox("Select ID to Delete", filtered_df['id'].tolist())
        if st.button("Delete Expense"):
            db.delete_expense(expense_to_delete)
            st.success(f"Deleted ID {expense_to_delete}")
            st.rerun()
            
        st.markdown("---")
        
        # Export to Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            display_df.to_excel(writer, index=False, sheet_name='Expenses')
        excel_data = output.getvalue()
        
        st.download_button(
            label="📥 Export to Excel",
            data=excel_data,
            file_name=f"expenses_{selected_month}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
