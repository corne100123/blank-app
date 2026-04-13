import streamlit as st
import sqlite3
import os
import hashlib

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
    st.markdown("**Admin access:** Login with an Admin account to manage users and create new accounts.")
    st.markdown("Use the admin username and password to access the User Management panel.")
    st.info("Default admin credentials: `admin` / `usizo2026` (if not changed)")

    with st.form("login"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            # Check credentials against database
            try:
                with get_db() as conn:
                    import hashlib
                    password_hash = hashlib.sha256(password.encode()).hexdigest()
                    user = conn.execute("""
                        SELECT username, role, full_name FROM users
                        WHERE username = ? AND password_hash = ? AND is_active = 1
                    """, (username, password_hash)).fetchone()

                    if user:
                        st.session_state.role = user[1]  # role
                        st.session_state.username = user[0]  # username
                        st.session_state.full_name = user[2]  # full_name

                        # Update last login
                        conn.execute(
                            "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE username = ?",
                            (username,)
                        )
                        conn.commit()

                        st.rerun()
                    else:
                        st.error("Invalid username or password, or account is inactive")
            except Exception as e:
                st.error(f"Login error: {e}")
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
    # --- DESKTOP VIEW (MANAGER/ADMIN) ---
    if role == "Admin":
        st.sidebar.title("👑 USIZO Admin")
        st.sidebar.caption("Full System Administration")
        menu = ["👥 User Management", "🏠 Dashboard", "👤 Onboarding", "📝 Client Editor", "➕ Loan Wizard", "💸 Payments", "📊 Reports", "📄 Invoices"]
    else:  # Manager
        st.sidebar.title("🏢 USIZO Manager")
        st.sidebar.caption("Full System Access")
        menu = ["🏠 Dashboard", "👤 Onboarding", "📝 Client Editor", "➕ Loan Wizard", "💸 Payments", "📊 Reports", "📄 Invoices"]

    choice = st.sidebar.radio("Admin Menu" if role == "Admin" else "Manager Menu", menu)

    # Routing logic
    if choice == "👥 User Management" and role == "Admin":
        from tools import user_management
        user_management.run(get_db)
    elif choice == "🏠 Dashboard":
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
    elif choice == "📄 Invoices":
        from tools import invoice_tool
        invoice_tool.run(get_db)

if st.sidebar.button("Logout"):
    st.session_state.role = None
    st.rerun()