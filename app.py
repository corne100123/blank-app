import streamlit as st
import sqlite3
import os

# --- 1. SETUP ---
st.set_page_config(page_title="USIZO Suite", layout="wide")

if 'role' not in st.session_state:
    st.session_state.role = None

def get_db():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return sqlite3.connect(os.path.join(base_dir, "NewLoanManager.db"))

# --- 2. LOGIN WITH ROLES ---
if not st.session_state.role:
    st.title("🔐 USIZO Login")
    with st.form("login"):
        user = st.text_input("Username")
        pwd = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            if user == "admin" and pwd == "usizo2026":
                st.session_state.role = "Manager"
                st.rerun()
            elif user == "agent" and pwd == "field2026":
                st.session_state.role = "Agent"
                st.rerun()
            else:
                st.error("Invalid credentials")
    st.stop()

# --- 3. THE TWO DIFFERENT LOOKS ---
role = st.session_state.role

if role == "Agent":
    # --- MOBILE/TABLET VIEW (AGENT) ---
    st.sidebar.title("📱 USIZO Mobile")
    st.sidebar.caption(f"Logged in: {role}")
    
    # Agents get a simplified, big-button menu
    menu = ["🏠 Today's Collections", "👤 New Client", "➕ Issue Loan"]
    choice = st.sidebar.radio("Main Menu", menu)
    
    if choice == "🏠 Today's Collections":
        from tools import payments_tool
        payments_tool.run(get_db, None)
    elif choice == "👤 New Client":
        from tools import onboarding
        onboarding.run(get_db, None)
    elif choice == "➕ Issue Loan":
        from tools import wizard
        wizard.run(get_db, None)

else:
    # --- DESKTOP VIEW (MANAGER) ---
    st.sidebar.title("🏢 USIZO Manager")
    st.sidebar.caption("Full System Access")
    
    menu = ["🏠 Dashboard", "👤 Onboarding", "📝 Client Editor", "➕ Loan Wizard", "💸 Payments", "📊 Reports"]
    choice = st.sidebar.radio("Admin Menu", menu)

    # ... routing logic for Manager (same as your previous app.py) ...
    if choice == "🏠 Dashboard":
        from tools import dashboard
        dashboard.run(get_db)
    elif choice == "👤 Onboarding":
        from tools import onboarding
        onboarding.run(get_db, None)
    elif choice == "📝 Client Editor":
        from tools import client_editor
        client_editor.run(get_db)
    elif choice == "➕ Loan Wizard":
        from tools import wizard
        wizard.run(get_db, None)
    elif choice == "💸 Payments":
        from tools import payments_tool
        payments_tool.run(get_db, None)
    elif choice == "📊 Reports":
        from tools import reports
        reports.run(get_db)

if st.sidebar.button("Logout"):
    st.session_state.role = None
    st.rerun()