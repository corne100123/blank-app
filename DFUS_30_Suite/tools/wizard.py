import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime

# --- LOAN PACKAGE CONFIGURATION ---
LOAN_PACKAGES = {
    "R 850 (Principal: R 600)": {"principal": 600.0, "total": 850.0},
    "R 1130 (Principal: R 800)": {"principal": 800.0, "total": 1130.0},
    "R 1400 (Principal: R 1000)": {"principal": 1000.0, "total": 1400.0}
}

# --- 2. HELPER: NCA CALCULATIONS ---
def calculate_nca_min_expense(gross):
    """NCA Regulation 23A Minimum Expense Norms"""
    if gross <= 800: return 0
    elif gross <= 6250: return 800 + (gross - 800) * 0.0675
    elif gross <= 25000: return 1167.88 + (gross - 6250) * 0.09
    elif gross <= 50000: return 2855.38 + (gross - 25000) * 0.082
    else: return 4905.38 + (gross - 50000) * 0.0675

# --- 3. MAIN LOAN TOOL ---
def run(get_db, audit_tool_ignored):
    st.header("💸 New Loan Issue Tool")
    
    # --- STEP 1: FIND THE CUSTOMER (UPDATED) ---
    st.subheader("1. Select Borrower")

    # We fetch ALL clients first to populate the dropdown
    # This solves the "I can't find them" issue immediately.
    client_list = []
    try:
        with get_db() as conn:
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
            
            # Agent Allocation (Admin/Manager only)
            agent_id_override = None
            if st.session_state.get('role') in ['Admin', 'Manager']:
                try:
                    with get_local_connection() as conn:
                        agents_df = pd.read_sql_query("SELECT user_id, full_name, username FROM users WHERE role = 'Agent' AND is_active = 1", conn)
                        if not agents_df.empty:
                            agent_options = {f"{r['full_name']} ({r['username']})": r['user_id'] for _, r in agents_df.iterrows()}
                            selected_agent_label = st.selectbox("Allocate to Agent", options=list(agent_options.keys()))
                            agent_id_override = agent_options[selected_agent_label]
                except Exception as e:
                    st.error(f"Error loading agents: {e}")

            with c1:
                loan_pkg = st.selectbox("Loan Package (Repayment amount)", options=list(LOAN_PACKAGES.keys()) + ["Custom"])
                if loan_pkg != "Custom":
                    principal = LOAN_PACKAGES[loan_pkg]["principal"]
                    st.info(f"Principal (Cash Out): R {principal:,.2f}")
                else:
                    principal = st.number_input("Principal Amount (Cash Out) (R)", min_value=100.0, step=100.0, value=1000.0)
                
                days = st.selectbox("Loan Term", ["30 Days", "1 Month"])
            
            with c2:
                if loan_pkg != "Custom":
                    total_repay = LOAN_PACKAGES[loan_pkg]["total"]
                    st.caption(f"Fixed Logic: Total Repayment R {total_repay:,.2f}")
                else:
                    # Standard Fees for custom amounts
                    initiation_fee = min(principal * 0.15, 1000) 
                    service_fee = 60.0 
                    interest = principal * 0.05 
                    total_repay = principal + initiation_fee + service_fee + interest
                    st.caption(f"Init Fee: R{initiation_fee:.2f} | Srv Fee: R{service_fee:.2f} | Int: R{interest:.2f}")
            
            st.metric("Total Repayment Amount", f"R {total_repay:,.2f}")
            
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

                            # Determine agent_id (Admin selection or current user)
                            if agent_id_override is not None:
                                agent_id = agent_id_override
                            else:
                                agent_username = st.session_state.get('username')
                                if agent_username:
                                    agent_res = cursor.execute("SELECT user_id FROM users WHERE username = ?", (agent_username,)).fetchone()
                                    agent_id = agent_res[0] if agent_res else None
                                else:
                                    agent_id = None

                            cursor.execute("""
                                INSERT INTO loans (client_id, principal, balance, status, due_date, agent_id)
                                VALUES (?, ?, ?, 'Active', DATE('now', '+30 days'), ?)
                            """, (int(client['client_id']), float(principal), float(total_repay), agent_id))

                            conn.commit()
                            st.balloons()
                            st.success("Loan Issued Successfully!")
                    except Exception as e:
                        st.error(f"Database Error: {e}")
                else:
                    st.error("Cannot issue loan: Affordability check failed.")