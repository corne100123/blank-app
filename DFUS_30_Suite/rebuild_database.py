import sqlite3
import os

db_path = "NewLoanManager.db"

def rebuild_clients():
    print(f"🔧 Connecting to {db_path}...")
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
    cursor.execute("DROP TABLE IF EXISTS clients")
    cursor.execute("DROP TABLE IF EXISTS loans")
    cursor.execute("DROP TABLE IF EXISTS payment_history")
    cursor.execute("DROP TABLE IF EXISTS expenses")
    print("✅ Old tables deleted.")

    # 3. CREATE THE NEW TABLES (The 'Correct' Structure)
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
            due_date TEXT,
            principal REAL,
            balance REAL,
            amount_paid REAL DEFAULT 0.0,
            status TEXT DEFAULT 'Active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(client_id) REFERENCES clients(client_id)
        )
    """)
    print("✅ Loans table created.")

    print("--- 🔨 Building New 'Payment History' Table ---")
    cursor.execute("""
        CREATE TABLE payment_history (
            payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            loan_id INTEGER,
            amount REAL,
            date TEXT,
            type TEXT,
            FOREIGN KEY(loan_id) REFERENCES loans(loan_id)
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

    # 4. INSERT A TEST CLIENT (So the tool works immediately)
    print("--- 🌱 Seeding Test Data ---")
    cursor.execute("""
        INSERT INTO clients (first_name, last_name, id_number, phone, total_gross, status) 
        VALUES ('John', 'Doe', '9901015000080', '0821234567', 15000, 'Active')
    """)
    print("✅ Test Client 'John Doe' added.")

    # Insert a test loan
    cursor.execute("""
        INSERT INTO loans (client_id, due_date, principal, balance, amount_paid, status)
        VALUES (1, '2026-04-30', 5000.0, 5000.0, 0.0, 'Active')
    """)
    print("✅ Test Loan added.")

    # Insert a test payment record
    cursor.execute("""
        INSERT INTO payment_history (loan_id, amount, date, type)
        VALUES (1, 0.0, '2026-04-01', 'Initial')
    """)
    print("✅ Test payment history record added.")

    conn.commit()
    conn.close()
    print("\n🎉 REBUILD COMPLETE!")
    print("👉 Restart Streamlit and try the Loan Wizard again.")

if __name__ == "__main__":
    rebuild_clients()