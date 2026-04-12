import streamlit as st
import pandas as pd
import sqlite3

def get_local_connection():
    return sqlite3.connect("../NewLoanManager.db")

def run(get_db_ignored):
    st.header("🛠️ Comprehensive Client & Loan Editor")

    # --- 1. SEARCH & SELECT ---
    search_term = st.text_input("🔍 Search Client (Name, Last Name, or ID)", placeholder="Search...")

    if not search_term:
        st.info("Please search for a client to begin editing.")
        return

    with get_local_connection() as conn:
        query = f"""
            SELECT * FROM clients 
            WHERE first_name LIKE '%{search_term}%' 
            OR last_name LIKE '%{search_term}%' 
            OR id_number LIKE '%{search_term}%'
        """
        results = pd.read_sql_query(query, conn)

    if results.empty:
        st.warning("No clients found.")
        return

    results['display'] = results['first_name'] + " " + results['last_name'] + " (" + results['id_number'] + ")"
    selected_display = st.selectbox("Select Client", results['display'])
    client = results[results['display'] == selected_display].iloc[0]
    client_id = int(client['client_id'])

    st.markdown("---")

    # --- 2. MULTI-FUNCTION TABS ---
    tab_personal, tab_employment, tab_loans = st.tabs([
        "👤 Personal Details", 
        "🏢 Employment & Bank", 
        "💰 Loan Adjustments & Fees"
    ])

    # TAB 1: PERSONAL DETAILS
    with tab_personal:
        with st.form("personal_form"):
            c1, c2 = st.columns(2)
            new_first = c1.text_input("First Name", value=client['first_name'])
            new_last = c2.text_input("Last Name", value=client['last_name'])
            new_id = c1.text_input("ID Number", value=client['id_number'])
            new_phone = c2.text_input("Phone", value=client['phone'])
            new_addr = st.text_area("Address", value=client['address'])
            
            if st.form_submit_button("💾 Update Personal Info"):
                with get_local_connection() as conn:
                    conn.execute("UPDATE clients SET first_name=?, last_name=?, id_number=?, phone=?, address=? WHERE client_id=?",
                                (new_first, new_last, new_id, new_phone, new_addr, client_id))
                    conn.commit()
                st.success("Personal details updated.")

    # TAB 2: EMPLOYMENT & BANK
    with tab_employment:
        with st.form("employment_form"):
            e1, e2 = st.columns(2)
            new_emp = e1.text_input("Employer", value=client['employer'] if 'employer' in client else "")
            new_gross = e1.number_input("Gross Income", value=float(client['total_gross']) if 'total_gross' in client else 0.0)
            new_bank = e2.text_input("Bank", value=client['bank_name'] if 'bank_name' in client else "")
            new_acc = e2.text_input("Account No", value=client['account_no'] if 'account_no' in client else "")
            
            if st.form_submit_button("💾 Update Employment/Bank"):
                with get_local_connection() as conn:
                    conn.execute("UPDATE clients SET employer=?, total_gross=?, bank_name=?, account_no=? WHERE client_id=?",
                                (new_emp, new_gross, new_bank, new_acc, client_id))
                    conn.commit()
                st.success("Employment and Banking info updated.")

    # TAB 3: LOAN ADJUSTMENTS & FEES
    with tab_loans:
        st.subheader("Manage Active Loans")
        
        with get_local_connection() as conn:
            loans = pd.read_sql_query(f"SELECT * FROM loans WHERE client_id = {client_id}", conn)
        
        if loans.empty:
            st.info("This client has no existing loans.")
        else:
            # Select which loan to adjust
            loans['loan_display'] = "Loan #" + loans['loan_id'].astype(str) + " (Bal: R" + loans['balance'].astype(str) + ")"
            target_loan_str = st.selectbox("Select Loan to Edit", loans['loan_display'])
            target_loan = loans[loans['loan_display'] == target_loan_str].iloc[0]
            target_id = int(target_loan['loan_id'])

            st.markdown("#### Adjustments")
            with st.form("balance_adj_form"):
                col_bal1, col_bal2 = st.columns(2)
                
                # Manual Balance Overwrite
                new_bal = col_bal1.number_input("Overwrite Current Balance (R)", value=float(target_loan['balance']))
                
                # Status Change
                new_status = col_bal2.selectbox("Loan Status", ["Active", "Settled", "Bad Debt", "Default"], 
                                               index=["Active", "Settled", "Bad Debt", "Default"].index(target_loan['status']))
                
                st.caption("Warning: Changing the balance here directly overrides the ledger calculations.")
                
                if st.form_submit_button("⚠️ Apply Balance/Status Change"):
                    with get_local_connection() as conn:
                        conn.execute("UPDATE loans SET balance=?, status=? WHERE loan_id=?", (new_bal, new_status, target_id))
                        conn.commit()
                    st.success("Loan balance and status updated.")
                    st.rerun()

            st.markdown("#### Apply Additional Fees")
            with st.form("fee_form"):
                f1, f2 = st.columns(2)
                fee_amount = f1.number_input("Fee Amount to Add (R)", min_value=0.0, step=10.0)
                fee_type = f2.selectbox("Fee Type", ["Admin Fee", "Arrears Penalty", "Legal Fee", "Service Fee"])
                
                if st.form_submit_button("➕ Add Fee to Balance"):
                    if fee_amount > 0:
                        with get_local_connection() as conn:
                            # 1. Increase the loan balance
                            conn.execute("UPDATE loans SET balance = balance + ? WHERE loan_id = ?", (fee_amount, target_id))
                            # 2. Record it in payment history as a negative 'Adjustment' for record-keeping if needed, 
                            # or just update the balance as we did here.
                            conn.commit()
                        st.success(f"Added R{fee_amount} {fee_type} to the loan balance.")
                        st.rerun()