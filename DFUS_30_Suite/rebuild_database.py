import sqlite3
import os
from config import _get_configured_db_path_for_scripts, get_default_db_path

def rebuild_clients(db_path=None, biz_name=None):
    if db_path is None:
        db_path = _get_configured_db_path_for_scripts()
    if not db_path:
        db_path = get_default_db_path()
    db_path = str(db_path)
    print(f"🔧 Connecting to {db_path}...")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. CHECK WHAT IS CURRENTLY THERE (For your info)
    print("--- Diagnosing Old Database ---")
    try:
        cursor.execute("PRAGMA table_info(clients)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"Old Columns found: {columns}")
    except Exception as e:
        print("Could not read old table.")

    # 2. DELETE THE BROKEN TABLES
    # We drop it entirely so we can rebuild it 100% correctly
    print("\n--- 🗑️ Deleting Broken Tables ---")
    cursor.execute("DROP TABLE IF EXISTS business_config")
    cursor.execute("DROP TABLE IF EXISTS clients")
    cursor.execute("DROP TABLE IF EXISTS loans")
    cursor.execute("DROP TABLE IF EXISTS payment_history")
    cursor.execute("DROP TABLE IF EXISTS expenses")
    cursor.execute("DROP TABLE IF EXISTS users")
    print("✅ Old tables deleted.")

    # 3. CREATE THE NEW TABLES (The 'Correct' Structure)
    print("--- 🔨 Building Business Config Table ---")
    cursor.execute("""
        CREATE TABLE business_config (
            config_id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_name TEXT NOT NULL,
            registration_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            cloud_sync_id TEXT
        )
    """)
    print("✅ Business config table created.")

    print("--- 🔨 Building New 'Users' Table ---")
    cursor.execute("""
        CREATE TABLE users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password_hash TEXT,
            full_name TEXT,
            email TEXT,
            phone TEXT,
            role TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    """)
    print("✅ Users table created.")

    print("--- 🔨 Building New 'Clients' Table ---")
    cursor.execute("""
        CREATE TABLE clients (
            client_id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT,
            last_name TEXT,
            id_number TEXT UNIQUE,
            phone TEXT,
            email TEXT,
            address TEXT,
            total_gross REAL DEFAULT 0.0,
            salary REAL DEFAULT 0.0,
            employer TEXT,
            work_days TEXT,
            pay_day TEXT,
            bank_name TEXT,
            account_no TEXT,
            status TEXT DEFAULT 'Active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✅ Clients table created.")

    print("--- 🔨 Building New 'Loans' Table ---")
    cursor.execute("""
        CREATE TABLE loans (
            loan_id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            agent_id INTEGER,
            due_date TEXT,
            principal REAL,
            balance REAL,
            amount_paid REAL DEFAULT 0.0,
            status TEXT DEFAULT 'Active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(client_id) REFERENCES clients(client_id),
            FOREIGN KEY(agent_id) REFERENCES users(user_id)
        )
    """)
    print("✅ Loans table created.")

    print("--- 🔨 Building New 'Payment History' Table ---")
    cursor.execute("""
        CREATE TABLE payment_history (
            payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            loan_id INTEGER,
            agent_id INTEGER,
            amount REAL,
            date TEXT,
            type TEXT,
            FOREIGN KEY(loan_id) REFERENCES loans(loan_id),
            FOREIGN KEY(agent_id) REFERENCES users(user_id)
        )
    """)
    print("✅ Payment history table created.")

    print("--- 🔨 Building New 'Expenses' Table ---")
    cursor.execute("""
        CREATE TABLE expenses (
            expense_id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT,
            amount REAL,
            date TEXT,
            category TEXT DEFAULT 'General'
        )
    """)
    print("✅ Expenses table created.")

    # 4. INSERT BUSINESS PROFILE
    if biz_name:
        print("--- 🔨 Inserting Business Profile ---")
        cursor.execute("""
            INSERT INTO business_config (business_name, cloud_sync_id)
            VALUES (?, NULL)
        """, (biz_name,))
        print("✅ Business profile recorded.")

    # 5. INSERT TEST DATA
    print("--- 🌱 Seeding Test Data ---")
    
    # Insert a test agent with columns matching user_management.py
    # Using a dummy hash for 'admin' (This matches hashlib.sha256('admin123').hexdigest())
    admin_pwd_hash = "240be518ebbafd630d06f022ce0d330c5e2310b988ce3920973a9414e8574d53"
    cursor.execute("""
        INSERT INTO users (username, password_hash, full_name, role, is_active)
        VALUES ('admin', ?, 'System Admin', 'Admin', 1)
    """, (admin_pwd_hash,))
    admin_id = cursor.lastrowid

    cursor.execute("""
        INSERT INTO clients (first_name, last_name, id_number, phone, total_gross, status) 
        VALUES ('John', 'Doe', '9901015000080', '0821234567', 15000, 'Active')
    """)
    print("✅ Test Client 'John Doe' added.")

    # Insert a test loan
    cursor.execute("""
        INSERT INTO loans (client_id, agent_id, due_date, principal, balance, amount_paid, status)
        VALUES (1, ?, '2026-04-30', 5000.0, 5000.0, 0.0, 'Active')
    """, (admin_id,))
    print("✅ Test Loan added.")

    # Insert a test payment record
    cursor.execute("""
        INSERT INTO payment_history (loan_id, agent_id, amount, date, type)
        VALUES (1, ?, 0.0, '2026-04-01', 'Initial')
    """, (admin_id,))
    print("✅ Test payment history record added.")

    conn.commit()
    conn.close()
    print("\n🎉 REBUILD COMPLETE!")
    print("👉 Restart Streamlit and try the Loan Wizard again.")

if __name__ == "__main__":
    rebuild_clients()