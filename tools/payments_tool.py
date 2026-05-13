import streamlit as st
import pandas as pd
from datetime import datetime
import sqlite3
from DFUS_30_Suite.config import _get_configured_db_path_for_scripts, get_default_db_path

# --- 1. DATABASE CONNECTION ---
def get_local_connection():
    db_path = _get_configured_db_path_for_scripts() or get_default_db_path()
    return sqlite3.connect(str(db_path))

# --- 2. MAIN PAYMENTS TOOL ---
def run(get_db_ignored, audit_tool_ignored):
    role = st.session_state.get('role', 'Manager')
    
    if role == 'Agent':
        # Mobile view: Daily Cashup and Payments
        st.header("💰 Daily Operations")
        
        tab1, tab2 = st.tabs(["💰 Daily Cashup", "💳 Record Payment"])
        
        with tab1:
            # Daily Cashup content
            today = datetime.now().strftime('%Y-%m-%d')
            
            with get_local_connection() as conn:
                # Total Payments Today
                pay_query = f"SELECT SUM(amount) as total FROM payment_history WHERE date = '{today}'"
                total_payments = pd.read_sql_query(pay_query, conn).iloc[0]['total'] or 0
                
                # Total Loans Issued Today
                loan_query = f"SELECT SUM(principal) as total FROM loans WHERE DATE(created_at) = '{today}'"
                total_loans = pd.read_sql_query(loan_query, conn).iloc[0]['total'] or 0
                
                # Total Expenses Today
                exp_query = f"SELECT SUM(amount) as total FROM expenses WHERE date = '{today}'"
                total_expenses = pd.read_sql_query(exp_query, conn).iloc[0]['total'] or 0
            
            net = total_payments + total_loans - total_expenses
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("💸 Payments Today", f"R{total_payments:.2f}")
            with col2:
                st.metric("➕ Loans Issued", f"R{total_loans:.2f}")
            with col3:
                st.metric("💼 Expenses", f"R{total_expenses:.2f}")
            with col4:
                st.metric("📊 Net Cashup", f"R{net:.2f}")
            
            st.markdown("---")
            
            # Record Expense
            with st.expander("➕ Record Expense"):
                with st.form("expense_form"):
                    desc = st.text_input("Description")
                    amt = st.number_input("Amount", min_value=0.01, step=0.01)
                    cat = st.selectbox("Category", ["Fuel", "Meals", "Transport", "Office", "Other"])
                    if st.form_submit_button("Add Expense"):
                        with get_local_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute("INSERT INTO expenses (description, amount, date, category) VALUES (?, ?, ?, ?)",
                                         (desc, amt, today, cat))
                            conn.commit()
                            st.success("Expense recorded!")
                            st.rerun()
            
            # Today's Payments List
            st.subheader("💳 Today's Payments")
            with get_local_connection() as conn:
                payments = pd.read_sql_query(f"""
                    SELECT ph.amount, ph.type, c.first_name, c.last_name
                    FROM payment_history ph
                    JOIN loans l ON ph.loan_id = l.loan_id
                    JOIN clients c ON l.client_id = c.client_id
                    WHERE ph.date = '{today}'
                """, conn)
            if not payments.empty:
                st.dataframe(payments, use_container_width=True)
            else:
                st.info("No payments today.")
            
            # Today's Loans
            st.subheader("➕ Today's Loans")
            with get_local_connection() as conn:
                loans = pd.read_sql_query(f"""
                    SELECT l.principal, c.first_name, c.last_name
                    FROM loans l
                    JOIN clients c ON l.client_id = c.client_id
                    WHERE DATE(l.created_at) = '{today}'
                """, conn)
            if not loans.empty:
                st.dataframe(loans, use_container_width=True)
            else:
                st.info("No loans issued today.")
            
            # Today's Expenses
            st.subheader("💼 Today's Expenses")
            with get_local_connection() as conn:
                expenses = pd.read_sql_query(f"SELECT description, amount, category FROM expenses WHERE date = '{today}'", conn)
            if not expenses.empty:
                st.dataframe(expenses, use_container_width=True)
            else:
                st.info("No expenses today.")
        
        with tab2:
            # Record Payment
            st.subheader("💳 Record Payment on Loan")
            
            # --- STEP 1: SELECT LOAN ---
            with get_local_connection() as conn:
                query = """
                    SELECT l.loan_id, c.first_name, c.last_name, l.principal, l.balance 
                    FROM loans l
                    JOIN clients c ON l.client_id = c.client_id
                    WHERE l.status = 'Active'
                """
                active_loans = pd.read_sql_query(query, conn)

            if active_loans.empty:
                st.info("No active loans found.")
            else:
                active_loans['display'] = (
                    active_loans['first_name'] + " " + 
                    active_loans['last_name'] + " (Owes: R" + 
                    active_loans['balance'].astype(str) + ")"
                )
                
                selected_loan_str = st.selectbox("Select Loan", active_loans['display'], key="agent_select_loan")
                loan_data = active_loans[active_loans['display'] == selected_loan_str].iloc[0]
                loan_id = int(loan_data['loan_id'])

                with st.form("agent_pay_form"):
                    pay_amount = st.number_input("Amount Paid (R)", min_value=0.0, value=float(loan_data['balance']), step=0.01, key="agent_pay_amount")
                    pay_type = st.selectbox("Method", ["Bank EFT", "Cash", "Debit Order", "Stop Order"], key="agent_pay_type")
                    pay_date = st.date_input("Date of Payment", datetime.now(), key="agent_pay_date")
                    
                    if st.form_submit_button("Confirm Payment"):
                        try:
                            with get_local_connection() as conn:
                                cursor = conn.cursor()
                                
                                cursor.execute("""
                                    INSERT INTO payment_history (loan_id, amount, date, type)
                                    VALUES (?, ?, ?, ?)
                                """, (loan_id, pay_amount, pay_date.strftime('%Y-%m-%d'), pay_type))
                                
                                # Update balance
                                new_balance = float(loan_data['balance']) - pay_amount
                                new_status = 'Settled' if new_balance <= 0 else 'Active'
                                
                                cursor.execute("UPDATE loans SET balance = ?, status = ? WHERE loan_id = ?", 
                                             (new_balance, new_status, loan_id))
                                
                                conn.commit()
                                st.success("✅ Payment Recorded!")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Payment Error: {e}")
    
    else:
        # Manager view: Payment processing
        st.header("💸 Payment Processing Hub")

        # --- STEP 1: SELECT LOAN ---
        with get_local_connection() as conn:
            query = """
                SELECT l.loan_id, c.first_name, c.last_name, l.principal, l.balance 
                FROM loans l
                JOIN clients c ON l.client_id = c.client_id
                WHERE l.status = 'Active'
            """
            active_loans = pd.read_sql_query(query, conn)

        if active_loans.empty:
            st.info("No active loans found.")
            return

        active_loans['display'] = (
            active_loans['first_name'] + " " + 
            active_loans['last_name'] + " (Owes: R" + 
            active_loans['balance'].astype(str) + ")"
        )
        
        selected_loan_str = st.selectbox("Select Loan", active_loans['display'])
        loan_data = active_loans[active_loans['display'] == selected_loan_str].iloc[0]
        loan_id = int(loan_data['loan_id'])

        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("💳 Record Payment")
            with st.form("pay_form"):
                pay_amount = st.number_input("Amount Paid (R)", min_value=0.0, value=float(loan_data['balance']), step=0.01)
                # Changed 'method' to 'type' to match your DB column name
                pay_type = st.selectbox("Method", ["Bank EFT", "Cash", "Debit Order", "Stop Order"])
                pay_date = st.date_input("Date of Payment", datetime.now())
                
                if st.form_submit_button("Confirm Payment"):
                    try:
                        with get_local_connection() as conn:
                            cursor = conn.cursor()
                            
                            # UPDATED: Using 'date' and 'type' to match your existing table
                            cursor.execute("""
                                INSERT INTO payment_history (loan_id, amount, date, type)
                                VALUES (?, ?, ?, ?)
                            """, (loan_id, pay_amount, pay_date.strftime('%Y-%m-%d'), pay_type))
                            
                            # Update balance
                            new_balance = float(loan_data['balance']) - pay_amount
                            new_status = 'Settled' if new_balance <= 0 else 'Active'
                            
                            cursor.execute("UPDATE loans SET balance = ?, status = ? WHERE loan_id = ?", 
                                         (new_balance, new_status, loan_id))
                            
                            conn.commit()
                            st.success("✅ Payment Recorded!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Payment Error: {e}")

        with col2:
            st.subheader("📄 History")
            with get_local_connection() as conn:
                # UPDATED: Selecting 'date' and 'type' instead of 'date_paid' and 'method'
                hist_query = f"SELECT date, amount, type FROM payment_history WHERE loan_id = {loan_id}"
                history = pd.read_sql_query(hist_query, conn)
            
            if not history.empty:
                st.dataframe(history, use_container_width=True)
            else:
                st.info("No payments recorded yet.")