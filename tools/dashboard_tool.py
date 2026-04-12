import streamlit as st
import pandas as pd
import plotly.express as px

def run(get_db):
    st.title("📊 USIZO Business Overview")
    
    with get_db() as conn:
        # Fetching all active loan data
        loans = pd.read_sql_query("SELECT * FROM loans WHERE status = 'Active'", conn)
        # Fetching all payment history
        payments = pd.read_sql_query("SELECT * FROM payment_history", conn)

    # --- TOP LEVEL METRICS ---
    col1, col2, col3 = st.columns(3)
    
    # Total Book Value (The full front-loaded amount you are owed)
    total_owed = loans['balance'].sum() if not loans.empty else 0.0
    # Total Principal Out (Just the raw money lent)
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
        st.subheader("Collection Progress")
        if not payments.empty:
            payments['date'] = pd.to_datetime(payments['date'])
            daily_pay = payments.groupby('date')['amount'].sum().reset_index()
            fig = px.line(daily_pay, x='date', y='amount', title="Daily Collections")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No payments recorded to show trends.")

    with c2:
        st.subheader("Loan Status Breakdown")
        if not loans.empty:
            status_counts = loans['status'].value_counts().reset_index()
            fig2 = px.pie(status_counts, values='count', names='status', hole=0.4)
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No active loans to analyze.")

    # --- OVERDUE ALERT ---
    st.subheader("🚩 Immediate Attention (Upcoming/Overdue)")
    if not loans.empty:
        loans['due_date'] = pd.to_datetime(loans['due_date'])
        # Simplified overdue logic for the dashboard
        overdue = loans[loans['due_date'] < pd.Timestamp.now()]
        if not overdue.empty:
            st.warning(f"There are {len(overdue)} loans past their due date.")
            st.dataframe(overdue[['loan_id', 'balance', 'due_date']], use_container_width=True)
        else:
            st.success("No loans are currently overdue.")