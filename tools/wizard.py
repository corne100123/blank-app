import os
import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# --- 1. DATABASE CONNECTION ---
def get_local_connection():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "NewLoanManager.db")
    return sqlite3.connect(db_path)

# --- 2. HELPER: NCA CALCULATIONS ---
def calculate_nca_min_expense(gross):
    """NCA Regulation 23A Minimum Expense Norms"""
    if gross <= 800: return 0
    elif gross <= 6250: return 800 + (gross - 800) * 0.0675
    elif gross <= 25000: return 1167.88 + (gross - 6250) * 0.09
    elif gross <= 50000: return 2855.38 + (gross - 25000) * 0.082
    else: return 4905.38 + (gross - 50000) * 0.0675

# --- 3. MAIN LOAN TOOL ---
def run(get_db_ignored, audit_tool_ignored):
    st.header("💸 New Loan Issue Tool")
    
    # --- STEP 1: FIND THE CUSTOMER (UPDATED) ---
    st.subheader("1. Select Borrower")

    # We fetch ALL clients first to populate the dropdown
    # This solves the "I can't find them" issue immediately.
    client_list = []
    try:
        with get_local_connection() as conn:
            df_all = pd.read_sql_query("SELECT client_id, first_name, last_name, id_number FROM clients", conn)
            if not df_all.empty:
                # Create a nice list of strings like "John Doe (900101...)"
                df_all['display_name'] = df_all['first_name'] + " " + df_all['last_name'] + " (" + df_all['id_number'] + ")"
                client_list = df_all['display_name'].tolist()
    except Exception as e:
        st.error(f"Database Read Error: {e}")

    # OPTION A: Search Box (Good for large lists)
    search_term = st.text_input("🔍 Search by Name or ID (Optional)", placeholder="Type to filter...")

    # OPTION B: The "Foolproof" Dropdown
    # If search term exists, we filter the list. If not, we show everyone.
    if search_term:
        filtered_list = [c for c in client_list if search_term.lower() in c.lower()]
    else:
        filtered_list = client_list

    if not filtered_list:
        st.warning("⚠️ No clients found in the database. The 'Ledger' data might be filler/test data.")
        st.info("Go to 'Onboarding' to add a real client.")
        selected_string = None
    else:
        selected_string = st.selectbox("👇 Select Client from List", filtered_list)

    # Logic to get the actual client data back from the selection
    if selected_string:
        # Extract ID number from the string "John Doe (900101...)"
        selected_id = selected_string.split('(')[-1].replace(')', '')
        
        with get_local_connection() as conn:
            client = pd.read_sql_query(f"SELECT * FROM clients WHERE id_number = '{selected_id}'", conn).iloc[0]
            
        st.success(f"Selected: {client['first_name']} {client['last_name']}")
        
        # --- STEP 2: CREATE THE LOAN (Only appears if client selected) ---
        st.markdown("---")
        with st.form("loan_contract_form"):
            c1, c2 = st.columns(2)
            with c1:
                principal = st.number_input("Principal Amount (Cash Out) (R)", min_value=100.0, step=100.0, value=1000.0)
                days = st.selectbox("Loan Term", ["30 Days", "1 Month"])
            
            with c2:
                st.subheader("Loan Fee Settings")
                init_percent = st.number_input("Initiation Fee %", min_value=0.0, max_value=50.0, value=15.0, step=0.5)
                init_cap = st.number_input("Initiation Fee Cap (R)", min_value=0.0, value=1000.0, step=50.0)
                service_fee = st.number_input("Service Fee (R)", min_value=0.0, value=60.0, step=5.0)
                interest_rate = st.number_input("Interest Rate %", min_value=0.0, max_value=50.0, value=5.0, step=0.1)

                extra_fee_1_label = st.text_input("Additional Fee 1 Label", value="Admin Fee")
                extra_fee_1_amount = st.number_input("Additional Fee 1 Amount (R)", min_value=0.0, value=0.0, step=10.0)
                extra_fee_2_label = st.text_input("Additional Fee 2 Label", value="Legal Fee")
                extra_fee_2_amount = st.number_input("Additional Fee 2 Amount (R)", min_value=0.0, value=0.0, step=10.0)

                initiation_fee = min(principal * (init_percent / 100), init_cap)
                interest = principal * (interest_rate / 100)
                additional_fees = extra_fee_1_amount + extra_fee_2_amount
                fee_display = f"Init R{initiation_fee:.2f} | Srv R{service_fee:.2f} | Int R{interest:.2f}"
                if extra_fee_1_amount > 0:
                    fee_display += f" | {extra_fee_1_label}: R{extra_fee_1_amount:.2f}"
                if extra_fee_2_amount > 0:
                    fee_display += f" | {extra_fee_2_label}: R{extra_fee_2_amount:.2f}"
                st.caption(fee_display)

            total_repay = principal + initiation_fee + service_fee + interest + additional_fees
            
            st.metric("Total Repayment Amount", f"R {total_repay:,.2f}")
            
            with st.expander("💰 Fee Breakdown"):
                st.write(f"Principal: R{principal:,.2f}")
                st.write(f"Initiation Fee ({init_percent}%): R{initiation_fee:,.2f}")
                st.write(f"Service Fee: R{service_fee:,.2f}")
                st.write(f"Interest ({interest_rate}%): R{interest:,.2f}")
                if extra_fee_1_amount > 0:
                    st.write(f"{extra_fee_1_label}: R{extra_fee_1_amount:,.2f}")
                if extra_fee_2_amount > 0:
                    st.write(f"{extra_fee_2_label}: R{extra_fee_2_amount:,.2f}")
                st.write(f"**Total: R{total_repay:,.2f}**")
            
            # --- GUARD RAILS (NCA) ---
            gross = client['total_gross'] if 'total_gross' in client else 0.0
            min_exp = calculate_nca_min_expense(gross)
            disposable = gross - min_exp
            
            if total_repay > disposable:
                st.error(f"⚠️ WARNING: Affordability Fail. (Disposable: R {disposable:,.2f})")
                approve_anyway = st.checkbox("Override (Manager Authorization)")
            else:
                st.success(f"✅ Affordability Passed. (Disposable: R {disposable:,.2f})")
                approve_anyway = True

            submitted_loan = st.form_submit_button("🚀 Approve & Issue Loan")
            
            if submitted_loan:
                if approve_anyway:
                    try:
                        with get_local_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute("""
                                INSERT INTO loans (client_id, principal, balance, status, due_date)
                                VALUES (?, ?, ?, 'Active', DATE('now', '+30 days'))
                            """, (int(client['client_id']), float(principal), float(total_repay)))
                            
                            conn.commit()
                            st.balloons()
                            st.success("Loan Issued Successfully!")
                    except Exception as e:
                        st.error(f"Database Error: {e}")
                else:
                    st.error("Cannot issue loan: Affordability check failed.")