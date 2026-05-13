"""
Client CRM Module - Core Data Component
Manages client/customer information and relationships
"""
import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class Client:
    """Client data structure"""
    client_id: Optional[int] = None
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    phone: str = ""
    physical_address: str = ""
    postal_address: str = ""
    id_number: str = ""
    tax_id: str = ""  # Client's VAT/TRN if applicable
    client_type: str = "Individual"  # Individual, Business, Government
    credit_limit: float = 0.0
    payment_terms: str = "30 days"
    notes: str = ""
    is_active: bool = True
    created_date: Optional[str] = None
    last_updated: Optional[str] = None

class ClientCRM:
    """Manages client data in SQLite database"""

    def __init__(self, db_path: str = None):
        if db_path is None:
            data_dir = Path(__file__).parent.parent / "data"
            data_dir.mkdir(exist_ok=True)
            db_path = data_dir / "clients.db"

        self.db_path = str(db_path)
        self._init_db()

    def _init_db(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS clients (
                    client_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    email TEXT,
                    phone TEXT,
                    physical_address TEXT,
                    postal_address TEXT,
                    id_number TEXT,
                    tax_id TEXT,
                    client_type TEXT DEFAULT 'Individual',
                    credit_limit REAL DEFAULT 0.0,
                    payment_terms TEXT DEFAULT '30 days',
                    notes TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                    last_updated TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indexes for better performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_clients_email ON clients(email)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_clients_id_number ON clients(id_number)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_clients_active ON clients(is_active)")

    def create_client(self, client: Client) -> int:
        """Create a new client and return client_id"""
        now = datetime.now().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO clients (
                    first_name, last_name, email, phone, physical_address,
                    postal_address, id_number, tax_id, client_type,
                    credit_limit, payment_terms, notes, is_active,
                    created_date, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                client.first_name, client.last_name, client.email, client.phone,
                client.physical_address, client.postal_address, client.id_number,
                client.tax_id, client.client_type, client.credit_limit,
                client.payment_terms, client.notes, client.is_active,
                now, now
            ))

            client_id = cursor.lastrowid
            return client_id

    def get_client(self, client_id: int) -> Optional[Client]:
        """Get client by ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM clients WHERE client_id = ?", (client_id,))

            row = cursor.fetchone()
            if row:
                return Client(**dict(row))
            return None

    def update_client(self, client: Client) -> bool:
        """Update existing client"""
        if not client.client_id:
            return False

        client.last_updated = datetime.now().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE clients SET
                    first_name = ?, last_name = ?, email = ?, phone = ?,
                    physical_address = ?, postal_address = ?, id_number = ?,
                    tax_id = ?, client_type = ?, credit_limit = ?,
                    payment_terms = ?, notes = ?, is_active = ?,
                    last_updated = ?
                WHERE client_id = ?
            """, (
                client.first_name, client.last_name, client.email, client.phone,
                client.physical_address, client.postal_address, client.id_number,
                client.tax_id, client.client_type, client.credit_limit,
                client.payment_terms, client.notes, client.is_active,
                client.last_updated, client.client_id
            ))

            return conn.total_changes > 0

    def delete_client(self, client_id: int) -> bool:
        """Soft delete client (set inactive)"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE clients SET is_active = 0, last_updated = ? WHERE client_id = ?",
                (datetime.now().isoformat(), client_id)
            )
            return conn.total_changes > 0

    def search_clients(self, query: str, active_only: bool = True) -> List[Client]:
        """Search clients by name, email, or ID number"""
        search_term = f"%{query}%"

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            if active_only:
                cursor = conn.execute("""
                    SELECT * FROM clients
                    WHERE is_active = 1 AND (
                        first_name LIKE ? OR last_name LIKE ? OR
                        email LIKE ? OR id_number LIKE ? OR
                        phone LIKE ?
                    )
                    ORDER BY last_name, first_name
                """, (search_term, search_term, search_term, search_term, search_term))
            else:
                cursor = conn.execute("""
                    SELECT * FROM clients
                    WHERE first_name LIKE ? OR last_name LIKE ? OR
                          email LIKE ? OR id_number LIKE ? OR
                          phone LIKE ?
                    ORDER BY last_name, first_name
                """, (search_term, search_term, search_term, search_term, search_term))

            return [Client(**dict(row)) for row in cursor.fetchall()]

    def get_all_clients(self, active_only: bool = True) -> List[Client]:
        """Get all clients"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            if active_only:
                cursor = conn.execute("SELECT * FROM clients WHERE is_active = 1 ORDER BY last_name, first_name")
            else:
                cursor = conn.execute("SELECT * FROM clients ORDER BY last_name, first_name")

            return [Client(**dict(row)) for row in cursor.fetchall()]

    def get_client_summary(self, client_id: int) -> Dict:
        """Get client summary with outstanding balance and invoice count"""
        with sqlite3.connect(self.db_path) as conn:
            # This would integrate with invoice system - placeholder for now
            return {
                "total_invoices": 0,
                "outstanding_balance": 0.0,
                "last_invoice_date": None
            }

    def validate_client(self, client: Client) -> Dict[str, str]:
        """Validate client data"""
        errors = {}

        if not client.first_name.strip():
            errors["first_name"] = "First name is required"

        if not client.last_name.strip():
            errors["last_name"] = "Last name is required"

        if client.email and "@" not in client.email:
            errors["email"] = "Invalid email format"

        if client.credit_limit < 0:
            errors["credit_limit"] = "Credit limit cannot be negative"

        return errors

# Global instance for easy access
client_crm = ClientCRM()

def get_client_crm() -> ClientCRM:
    """Convenience function to get client CRM instance"""
    return client_crm