import os
from supabase import create_client, Client

# Initialize Supabase client
# Ensure SUPABASE_URL and SUPABASE_KEY are set in your environment or secrets
url: str = os.environ.get("SUPABASE_URL", "")
key: str = os.environ.get("SUPABASE_KEY", "")

supabase: Client = create_client(url, key)

# ==========================================
# 1. EXPENSES & INCOME TRANSACTIONS
# ==========================================

def fetch_expenses():
    """Fetches all transactions (Expenses and Incomes) from Supabase."""
    response = supabase.table("expenses").select("*").order("date", desc=True).execute()
    return response.data

def add_transaction(date, category, amount, payment_mode, note="", trans_type="EXPENSE"):
    """
    Adds a new transaction (EXPENSE or INCOME) and automatically updates wallet balance.
    """
    data = {
        "date": str(date),
        "category": category,
        "amount": float(amount),
        "payment_mode": payment_mode,
        "note": note,
        "type": trans_type
    }
    supabase.table("expenses").insert(data).execute()
    
    # Automatically update corresponding wallet balance
    is_online = payment_mode in ["UPI", "Debit Card", "Online"]
    wallets = get_wallets()
    
    if trans_type == "EXPENSE":
        if is_online:
            update_wallets(wallets['online_balance'] - float(amount), wallets['offline_balance'])
        else:
            update_wallets(wallets['online_balance'], wallets['offline_balance'] - float(amount))
    elif trans_type == "INCOME":
        if is_online:
            update_wallets(wallets['online_balance'] + float(amount), wallets['offline_balance'])
        else:
            update_wallets(wallets['online_balance'], wallets['offline_balance'] + float(amount))

def delete_expense(expense_id):
    """Deletes a transaction by ID."""
    supabase.table("expenses").delete().eq("id", expense_id).execute()

# ==========================================
# 2. WALLET MANAGEMENT
# ==========================================

def get_wallets():
    """Fetches current Online and Offline cash balances."""
    response = supabase.table("wallets").select("*").eq("id", 1).execute()
    if response.data:
        return response.data[0]
    return {"online_balance": 0.0, "offline_balance": 0.0}

def update_wallets(online_balance, offline_balance):
    """Updates Online and Offline cash balances directly."""
    supabase.table("wallets").update({
        "online_balance": float(online_balance),
        "offline_balance": float(offline_balance)
    }).eq("id", 1).execute()

def transfer_funds(amount, direction="ONLINE_TO_CASH"):
    """
    Transfers money between Online and Cash wallets (ATM Withdrawal/Deposit).
    Does not log as an expense.
    """
    wallets = get_wallets()
    online = float(wallets['online_balance'])
    offline = float(wallets['offline_balance'])
    amt = float(amount)

    if direction == "ONLINE_TO_CASH":
        if online >= amt:
            update_wallets(online - amt, offline + amt)
            return True, "Transferred ₹{:,.2f} from Online to Cash!".format(amt)
        return False, "Insufficient Online Balance!"
    else: # CASH_TO_ONLINE
        if offline >= amt:
            update_wallets(online + amt, offline - amt)
            return True, "Transferred ₹{:,.2f} from Cash to Online!".format(amt)
        return False, "Insufficient Cash Balance!"
