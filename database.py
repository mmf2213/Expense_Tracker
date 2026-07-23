import psycopg2
import pandas as pd
import streamlit as st

def get_connection():
    """Connects to Supabase PostgreSQL database using Streamlit secrets."""
    return psycopg2.connect(st.secrets["SUPABASE_URL"])

def init_db():
    """Table is created via Supabase SQL Editor."""
    pass

def add_expense(date, category, amount, payment_mode, note):
    """Inserts a new expense record into Supabase."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO expense (date, category, amount, payment_mode, note)
        VALUES (%s, %s, %s, %s, %s)
    """, (str(date), category, amount, payment_mode, note))
    conn.commit()
    conn.close()

def fetch_expenses():
    """Retrieves all expenses from Supabase as a Pandas DataFrame."""
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM expense ORDER BY date DESC", conn)
    conn.close()
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
    return df

def delete_expense(expense_id):
    """Deletes an expense record by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM expense WHERE id = %s", (expense_id,))
    conn.commit()
    conn.close()