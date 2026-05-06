import streamlit as st
import sqlite3
import os
import hashlib
import json
import requests
from rebuild_database import rebuild_clients

# --- 0. HYBRID CONFIGURATION ---
VERSION = "1.0.0"
CONFIG_PATH = os.path.expanduser("~/.fus30_config.json")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r') as f:
            try:
                return json.load(f)
            except (json.JSONDecodeError, IOError):
                return None
    return None

def save_config(biz_name, db_path):
    config = {"business_name": biz_name, "db_path": db_path}
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f)
    return config

# --- 1. SESSION & BRANDING ---
if 'config' not in st.session_state:
    st.session_state.config = load_config()

if 'role' not in st.session_state:
    st.session_state.role = None

app_name = st.session_state.config['business_name'] if st.session_state.config else "FUS30"
st.set_page_config(page_title=f"{app_name} | FUS30 Suite", layout="wide")

@st.cache_data(ttl=3600)
def check_for_updates():
    """Cloud-Light: Check for version updates from GitHub."""
    try:
        # Replace with your actual GitHub raw URL for version.json
        update_url = "https://raw.githubusercontent.com/your-org/fus30/main/version.json"
        response = requests.get(update_url, timeout=1)
        if response.status_code == 200:
            remote_version = response.json().get("version")
            if remote_version and remote_version != VERSION:
                st.sidebar.info(f"✨ Update Available: {remote_version}")
    except:
        pass

# --- SETUP WIZARD (First Run Only) ---
if not st.session_state.config:
    st.title("⚙️ FUS30 Setup Wizard")
    st.markdown("### Welcome to the FUS30 Desktop Interface")
    st.write("Please configure your local environment to continue.")
    
    with st.form("setup_wizard"):
        biz_name = st.text_input("Business Name", placeholder="e.g. Centurion Microfinance")
        default_db = os.path.join(BASE_DIR, "fus30_operational.db")
        db_path = st.text_input("Local Data Storage Path (SQLite)", value=default_db)
        
        st.info("💡 Cloud-Light Sync: Your Business Name and ID will be registered to the FUS30 cloud registry, but your operational data stays in the local SQLite file.")
        
        if st.form_submit_button("Initialize System"):
            if biz_name and db_path:
                # Mock Cloud Registration Placeholder
                # register_business_to_cloud(biz_name) 
                st.session_state.config = save_config(biz_name, db_path)
                
                # Initialize the new DB if it doesn't exist
                if not os.path.exists(db_path):
                    rebuild_clients(db_path=db_path)
                
                st.success("Setup complete! Refreshing application...")
                st.rerun()
            else:
                st.error("Both Business Name and Database Path are required.")
    st.stop()

def init_db():
    """Ensures the local database is initialized."""
    if st.session_state.config:
        db_path = st.session_state.config.get('db_path')
        if not os.path.exists(db_path):
            with st.spinner("Initializing local operational database..."):
                rebuild_clients(db_path=db_path)

def get_db():
    """Injected database connection using the configured local path."""
    try:
        return sqlite3.connect(st.session_state.config['db_path'])
    except:
        return sqlite3.connect(os.path.join(BASE_DIR, "NewLoanManager.db"))

# Run initialization
init_db()

# --- 2. LOGIN WITH ROLES ---
if not st.session_state.role:
    st.title(f"🔐 {app_name} Login")
    check_for_updates()
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
                    # Ensure users table exists before querying
                    conn.execute("""
                        CREATE TABLE IF NOT EXISTS users (
                            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                            username TEXT UNIQUE,
                            password_hash TEXT,
                            role TEXT,
                            full_name TEXT,
                            email TEXT,
                            phone TEXT,
                            is_active INTEGER DEFAULT 1,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            last_login TIMESTAMP
                        )
                    """)
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
                        # Fallback/bootstrap: allow default local credentials to create a user
                        if username == "admin" and password == "usizo2026":
                            default_role = "Admin"
                        elif username == "agent" and password == "field2026":
                            default_role = "Agent"
                        else:
                            default_role = None

                        if default_role:
                            try:
                                # Insert default user if missing
                                password_hash = hashlib.sha256(password.encode()).hexdigest()
                                conn.execute("""
                                    INSERT OR IGNORE INTO users (username, password_hash, role, full_name, is_active)
                                    VALUES (?, ?, ?, ?, 1)
                                """, (username, password_hash, default_role, username.capitalize()))
                                conn.commit()

                                st.session_state.role = default_role
                                st.session_state.username = username
                                st.session_state.full_name = username.capitalize()
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed to create bootstrap user: {e}")
                        else:
                            st.error("Invalid username or password, or account is inactive")
            except Exception as e:
                st.error(f"Login error: {e}")
    st.stop()

# --- 3. THE TWO DIFFERENT LOOKS ---
check_for_updates()
role = st.session_state.role

if role == "Agent":
    # --- MOBILE/TABLET VIEW (AGENT) ---
    st.sidebar.title(f"📱 {app_name} Mobile")
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
        st.sidebar.title(f"👑 {app_name} Admin")
        st.sidebar.caption("Full System Administration")
        menu = ["👥 User Management", "🏠 Dashboard", "👤 Onboarding", "📝 Client Editor", "➕ Loan Wizard", "💸 Payments", "📊 Reports", "📄 Invoices"]
    else:  # Manager
        st.sidebar.title(f"🏢 {app_name} Manager")
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