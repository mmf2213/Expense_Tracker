import os
import streamlit as st
from supabase import create_client, Client

# Initialize Supabase client
url: str = st.secrets.get("SUPABASE_URL") or os.environ.get("SUPABASE_URL", "")
key: str = st.secrets.get("SUPABASE_KEY") or os.environ.get("SUPABASE_KEY", "")

supabase: Client = create_client(url, key)

# ==========================================
# TRANSACTIONS
# ==========================================

def fetch_expenses():
    """Fetches all transactions from Supabase."""
    try:
        response = supabase.table("expenses").select("*").order("date", desc=True).execute()
        return response.data or []
    except Exception as e:
        st.error(f"Error fetching expenses: {e}")
        return []

def add_transaction(date, category, amount, payment_mode, note="", trans_type="EXPENSE"):
    """Adds a new transaction and updates wallet balances."""
    data = {
        "date": str(date),
        "category": category,
        "amount": float(amount),
        "payment_mode": payment_mode,
        "note": note or "",
        "type": trans_type
    }
    
    try:
        response = supabase.table("expenses").insert(data).execute()
    except Exception as e:
        st.error(f"Database Error: {e}")
        return None

    # Update corresponding wallet balance
    is_online = payment_mode in ["UPI", "Debit Card", "Online"]
    wallets = get_wallets()
    current_online = float(wallets.get('online_balance', 0.0))
    current_offline = float(wallets.get('offline_balance', 0.0))

    if trans_type == "EXPENSE":
        if is_online:
            update_wallets(current_online - float(amount), current_offline)
        else:
            update_wallets(current_online, current_offline - float(amount))
    elif trans_type == "INCOME":
        if is_online:
            update_wallets(current_online + float(amount), current_offline)
        else:
            update_wallets(current_online, current_offline + float(amount))
            
    return response

def delete_expense(expense_id):
    """Deletes a transaction by ID."""
    try:
        return supabase.table("expenses").delete().eq("id", expense_id).execute()
    except Exception as e:
        st.error(f"Error deleting expense: {e}")
        return None

# ==========================================
# WALLETS
# ==========================================

def get_wallets():
    """Fetches Online and Cash wallet balances."""
    try:
        response = supabase.table("wallets").select("*").eq("id", 1).execute()
        if response.data:
            return response.data[0]
    except Exception as e:
        st.error(f"Error fetching wallets: {e}")
        
    return {"id": 1, "online_balance": 0.0, "offline_balance": 0.0}

def update_wallets(online_balance, offline_balance):
    """Updates Online and Cash balances directly."""
    try:
        return supabase.table("wallets").update({
            "online_balance": float(online_balance),
            "offline_balance": float(offline_balance)
        }).eq("id", 1).execute()
    except Exception as e:
        st.error(f"Error updating wallets: {e}")
        return None

def transfer_funds(amount, direction="ONLINE_TO_CASH"):
    """Transfers funds between Online and Cash wallets."""
    wallets = get_wallets()
    online = float(wallets.get('online_balance', 0.0))
    offline = float(wallets.get('offline_balance', 0.0))
    amt = float(amount)

    if direction == "ONLINE_TO_CASH":
        if online >= amt:
            update_wallets(online - amt, offline + amt)
            return True, f"Transferred ₹{amt:,.2f} to Cash!"
        return False, "Insufficient Online Balance!"
    else:
        if offline >= amt:
            update_wallets(online + amt, offline - amt)
            return True, f"Transferred ₹{amt:,.2f} to Online!"
        return False, "Insufficient Cash Balance!"
