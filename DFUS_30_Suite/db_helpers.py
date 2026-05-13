"""
Database helper functions for FUS30.
Provides modular access to database operations.
"""
import sqlite3
from contextlib import contextmanager


@contextmanager
def get_db_connection(db_path):
    """Context manager for database connections."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


# ============= AGENT MANAGEMENT =============

def get_active_agents(db_path):
    """
    Fetches a list of all active agents.
    Returns list of dictionaries with user_id, username, and full_name.
    """
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_id, username, full_name
            FROM users
            WHERE role = 'agent' AND is_active = 1
            ORDER BY full_name ASC
        """)
        agents = [dict(row) for row in cursor.fetchall()]
    return agents


def get_agent_by_id(db_path, user_id):
    """Get agent details by user_id."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_id, username, full_name, email
            FROM users
            WHERE user_id = ? AND role = 'agent'
        """, (user_id,))
        agent = cursor.fetchone()
    return dict(agent) if agent else None


# ============= CLIENT MANAGEMENT =============

def create_client(db_path, first_name, last_name, id_number, phone, email, 
                  assigned_agent_id=None, address=None, salary=None, employer=None):
    """
    Create a new client and assign to an agent.
    
    Args:
        db_path: Path to database
        first_name: Client first name
        last_name: Client last name
        id_number: Client ID/passport number
        phone: Contact phone
        email: Client email
        assigned_agent_id: User ID of assigned agent (or None for unassigned)
        address: Physical address
        salary: Annual salary
        employer: Employer name
    
    Returns:
        client_id of newly created client, or None if error
    """
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO clients 
                (first_name, last_name, id_number, phone, email, assigned_agent_id, address, salary, employer)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (first_name, last_name, id_number, phone, email, assigned_agent_id, address, salary, employer))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError as e:
            print(f"Error creating client: {e}")
            return None


def get_clients_by_agent(db_path, agent_id):
    """
    Fetch all clients assigned to a specific agent.
    
    Args:
        db_path: Path to database
        agent_id: User ID of the agent
    
    Returns:
        List of client dictionaries
    """
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM clients
            WHERE assigned_agent_id = ?
            ORDER BY last_name, first_name ASC
        """, (agent_id,))
        clients = [dict(row) for row in cursor.fetchall()]
    return clients


def get_all_clients(db_path):
    """Fetch all clients in the system."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.*, u.full_name as agent_name
            FROM clients c
            LEFT JOIN users u ON c.assigned_agent_id = u.user_id
            ORDER BY c.last_name, c.first_name ASC
        """)
        clients = [dict(row) for row in cursor.fetchall()]
    return clients


def update_client_assignment(db_path, client_id, agent_id):
    """
    Reassign a client to a different agent.
    
    Args:
        db_path: Path to database
        client_id: Client ID
        agent_id: New agent user ID (or None to unassign)
    
    Returns:
        True if successful, False otherwise
    """
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE clients
                SET assigned_agent_id = ?
                WHERE client_id = ?
            """, (agent_id, client_id))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error updating client assignment: {e}")
            return False


# ============= BUSINESS PROFILE =============

def get_business_profile(db_path):
    """Get the business configuration."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM business_config LIMIT 1")
        profile = cursor.fetchone()
    return dict(profile) if profile else None


def update_business_profile(db_path, business_name, vat_number=None, address=None, 
                           banking_details=None):
    """
    Update business profile information.
    Stores as JSON in metadata field if needed.
    """
    profile = get_business_profile(db_path)
    
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        if profile:
            cursor.execute("""
                UPDATE business_config
                SET business_name = ?
                WHERE config_id = ?
            """, (business_name, profile['config_id']))
        else:
            cursor.execute("""
                INSERT INTO business_config (business_name)
                VALUES (?)
            """, (business_name,))
        conn.commit()
    return True


# ============= LOAN & INVOICE TRACKING =============

def create_invoice_record(db_path, client_id, agent_id, invoice_number, 
                         amount, due_date, invoice_data_json=None):
    """
    Record an invoice in the database for tracking and audit purposes.
    
    Args:
        db_path: Path to database
        client_id: Client ID
        agent_id: Agent who created invoice
        invoice_number: Unique invoice number
        amount: Invoice total amount
        due_date: Invoice due date
        invoice_data_json: Serialized invoice data for audit trail
    
    Returns:
        Invoice ID or None
    """
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO invoices 
                (client_id, agent_id, invoice_number, amount, due_date, status, data)
                VALUES (?, ?, ?, ?, ?, 'Draft', ?)
            """, (client_id, agent_id, invoice_number, amount, due_date, invoice_data_json))
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"Error creating invoice record: {e}")
            return None


def get_next_invoice_number(db_path, prefix="INV"):
    """
    Generate the next invoice number in sequence.
    Format: INV-2026-0001
    
    Args:
        db_path: Path to database
        prefix: Invoice prefix (default "INV")
    
    Returns:
        Next invoice number as string
    """
    from datetime import datetime
    
    year = datetime.now().year
    
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        # Count invoices created this year
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM invoices
            WHERE strftime('%Y', created_at) = ?
        """, (str(year),))
        count = cursor.fetchone()['count'] + 1
    
    return f"{prefix}-{year}-{count:04d}"


# ============= AUDIT & HISTORY =============

def log_invoice_action(db_path, invoice_id, action, agent_id, notes=None):
    """
    Log actions taken on invoices for audit trail.
    
    Args:
        db_path: Path to database
        invoice_id: Invoice ID
        action: Action type (e.g., 'created', 'sent', 'paid')
        agent_id: User ID of agent performing action
        notes: Additional notes
    """
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO invoice_audit (invoice_id, agent_id, action, notes)
            VALUES (?, ?, ?, ?)
        """, (invoice_id, agent_id, action, notes))
        conn.commit()


def get_client_invoice_history(db_path, client_id):
    """Fetch all invoices for a specific client."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM invoices
            WHERE client_id = ?
            ORDER BY created_at DESC
        """, (client_id,))
        invoices = [dict(row) for row in cursor.fetchall()]
    return invoices
