import streamlit as st
import pandas as pd
import sqlite3
from DFUS_30_Suite.config import _get_configured_db_path_for_scripts, get_default_db_path

# --- DATABASE CONNECTION ---
def get_local_connection():
    db_path = _get_configured_db_path_for_scripts() or get_default_db_path()
    return sqlite3.connect(str(db_path))

def run(get_db_ignored):
    st.title("📊 USIZO Business Overview")
    
    # We ignore the 'get_db_ignored' coming from app.py because it's broken (Postgres)
    # We use our own local connection instead.
    with get_local_connection() as conn:
        try:
            # Fetching all active loan data
            loans = pd.read_sql_query("SELECT * FROM loans WHERE status = 'Active'", conn)
            # Fetching all payment history
            payments = pd.read_sql_query("SELECT * FROM payment_history", conn)
        except Exception as e:
            st.error(f"Database Error: {e}")
            return

    # --- TOP LEVEL METRICS ---
    col1, col2, col3 = st.columns(3)
    
    # Total Book Value
    total_owed = loans['balance'].sum() if not loans.empty else 0.0
    # Total Principal Out
    total_principal = loans['principal'].sum() if not loans.empty else 0.0
    # Total Collected
    total_collected = payments['amount'].sum() if not payments.empty else 0.0

    col1.metric("Total Book Value (Owed)", f"R {total_owed:,.2f}")
    col2.metric("Principal Out", f"R {total_principal:,.2f}")
    col3.metric("Total Collected", f"R {total_collected:,.2f}")

    st.markdown("---")

    # --- VISUALS ---
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Collection Trends")
        if not payments.empty:
            payments['date'] = pd.to_datetime(payments['date'])
            daily_pay = payments.groupby('date')['amount'].sum()
            st.line_chart(daily_pay)
        else:
            st.info("No payments recorded yet.")

    with c2:
        st.subheader("Loan Book Distribution")
        if not loans.empty:
            chart_data = loans[['principal', 'balance']]
            st.bar_chart(chart_data)
        else:
            st.info("No active loans to show.")

    # --- OVERDUE ALERT LEDGER ---
    st.markdown("---")
    st.subheader("🚩 Overdue / Due Now Accounts")
    if not loans.empty:
        loans['due_date'] = pd.to_datetime(loans['due_date'])
        overdue = loans[loans['due_date'].dt.date <= pd.Timestamp.now().date()]
        if not overdue.empty:
            st.warning(f"Attention: {len(overdue)} accounts require collection.")
            st.table(overdue[['loan_id', 'balance', 'due_date']])
        else:
            st.success("All accounts are currently within their 30-day window.")