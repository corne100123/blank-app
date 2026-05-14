import sqlite3
import os
from config import _get_configured_db_path_for_scripts

# Pointing to the configured or default database location
db_path = _get_configured_db_path_for_scripts()
if not db_path:
    print("Error: Database path not found in configuration. Please run the main app setup first.")
    exit(1)


def _safe_add_column(cursor, table, definition):
    col_name = definition.split()[0]
    try:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {definition}")
        print(f"   -> Added missing column: {col_name} to {table}")
    except sqlite3.OperationalError:
        pass


def run_fix():
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    print(f"🔧 Connecting to database at: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("Checking 'tenants' table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tenants (
            tenant_id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_name TEXT NOT NULL,
            ncr_registration_number TEXT NOT NULL UNIQUE,
            address TEXT,
            email TEXT,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 1
        )
    """)

    print("Checking 'business_config' table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS business_config (
            config_id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id INTEGER,
            business_name TEXT NOT NULL,
            registration_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            cloud_sync_id TEXT
        )
    """)

    print("Checking 'users' table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id INTEGER NOT NULL,
            username TEXT NOT NULL,
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

    print("Checking 'agents' table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agents (
            agent_id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id INTEGER NOT NULL,
            user_id INTEGER,
            name TEXT NOT NULL,
            id_number TEXT,
            employee_code TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    print("Checking 'clients' table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            client_id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id INTEGER NOT NULL,
            first_name TEXT,
            last_name TEXT,
            id_number TEXT,
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
            assigned_agent_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    print("Checking 'reassignment_history' table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reassignment_history (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id INTEGER NOT NULL,
            client_id INTEGER NOT NULL,
            old_agent_id INTEGER,
            new_agent_id INTEGER,
            reason TEXT,
            changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    print("Checking 'loans' table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS loans (
            loan_id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id INTEGER NOT NULL,
            client_id INTEGER,
            agent_id INTEGER,
            principal REAL,
            balance REAL,
            status TEXT,
            due_date DATE
        )
    """)

    print("Checking 'payment_history' table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payment_history (
            payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id INTEGER NOT NULL,
            loan_id INTEGER,
            amount REAL,
            date_paid DATE,
            method TEXT
        )
    """)

    print("Checking 'expenses' table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            expense_id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id INTEGER NOT NULL,
            description TEXT,
            amount REAL,
            date TEXT,
            category TEXT DEFAULT 'General'
        )
    """)

    print("Checking 'invoices' table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            invoice_id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id INTEGER NOT NULL,
            client_id INTEGER,
            agent_id INTEGER,
            invoice_number TEXT UNIQUE,
            amount REAL,
            due_date TEXT,
            status TEXT DEFAULT 'Draft',
            data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    print("Checking 'invoice_audit' table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoice_audit (
            audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id INTEGER NOT NULL,
            invoice_id INTEGER,
            agent_id INTEGER,
            action TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    print("Checking 'cashups' table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cashups (
            cashup_id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id INTEGER NOT NULL,
            agent_id INTEGER,
            cash_on_hand_open REAL DEFAULT 0.0,
            withdraw REAL DEFAULT 0.0,
            rente REAL DEFAULT 0.0,
            single REAL DEFAULT 0.0,
            double REAL DEFAULT 0.0,
            returns REAL DEFAULT 0.0,
            zero REAL DEFAULT 0.0,
            new REAL DEFAULT 0.0,
            top_up REAL DEFAULT 0.0,
            petrol REAL DEFAULT 0.0,
            transport REAL DEFAULT 0.0,
            melon_mobile REAL DEFAULT 0.0,
            deposit_general REAL DEFAULT 0.0,
            deposit_fnb REAL DEFAULT 0.0,
            deposit_capitec REAL DEFAULT 0.0,
            active_accounts INTEGER DEFAULT 0,
            outstanding INTEGER DEFAULT 0,
            single_outstanding INTEGER DEFAULT 0,
            cash_on_hand_end REAL DEFAULT 0.0,
            new_loans_text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    print("Checking 'compliance_documents' table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS compliance_documents (
            document_id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id INTEGER NOT NULL,
            document_type TEXT,
            original_filename TEXT,
            stored_filename TEXT,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    print("\n✅ REPAIR COMPLETE. All tables should now match the code.")


if __name__ == "__main__":
    run_fix()
