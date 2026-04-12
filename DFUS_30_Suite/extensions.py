import pandas as pd
from datetime import datetime, timedelta

def calculate_31_day_schedule(principal, rate_percent, initiation_fee, admin_fee, life_cover):
    """
    Recoding the Margill 'Compute' logic for a standard 31-day loan.
    """
    interest_amt = principal * (rate_percent / 100)
    total_due = principal + interest_amt + initiation_fee + admin_fee + life_cover
    
    # Create the 'Results Table' structure matching the old software
    schedule = {
        "Description": ["Principal", "Interest (3%)", "Initiation Fee", "Admin Fee", "Life Cover", "TOTAL DUE"],
        "Amount": [principal, interest_amt, initiation_fee, admin_fee, life_cover, total_due]
    }
    return pd.DataFrame(schedule), total_due

def generate_ledger_view(conn, client_id):
    """
    Fetches the running ledger for a specific client.
    """
    query = f"""
    SELECT date_paid as 'Date', amount_paid as 'Credit', 'Payment' as 'Type'
    FROM payment_history 
    WHERE loan_id IN (SELECT loan_id FROM loans WHERE client_id = {client_id})
    """
    return pd.read_sql_query(query, conn)