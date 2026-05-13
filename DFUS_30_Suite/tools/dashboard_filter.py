"""
Dashboard Filtering Module for FUS30.
Provides role-based filtering so agents only see their assigned clients.
"""
import streamlit as st
import pandas as pd
from db_helpers import get_clients_by_agent, get_all_clients


class DashboardFilter:
    """Handles dashboard data filtering based on user role."""
    
    def __init__(self, user_id, role, db_path):
        self.user_id = user_id
        self.role = role
        self.db_path = db_path
    
    def should_filter_by_agent(self):
        """
        Determine if data should be filtered by agent.
        - Admin: See all
        - Agent: See only their clients
        - Viewer: See all (read-only)
        """
        return self.role == 'agent'
    
    def get_filtered_clients(self):
        """
        Get clients based on user role and permissions.
        """
        if self.should_filter_by_agent():
            # Agents only see their assigned clients
            return get_clients_by_agent(self.db_path, self.user_id)
        else:
            # Admin/Viewer see all clients
            return get_all_clients(self.db_path)
    
    def get_filtered_loans(self, conn):
        """
        Get loans based on user role.
        For agents: only loans from their assigned clients.
        For admin: all loans.
        """
        if self.should_filter_by_agent():
            # Get loans for agent's clients only
            query = """
                SELECT l.*, c.first_name, c.last_name
                FROM loans l
                JOIN clients c ON l.client_id = c.client_id
                WHERE c.assigned_agent_id = ?
                ORDER BY l.created_at DESC
            """
            df = pd.read_sql_query(query, conn, params=(self.user_id,))
        else:
            # Get all loans
            query = """
                SELECT l.*, c.first_name, c.last_name, u.full_name as agent_name
                FROM loans l
                JOIN clients c ON l.client_id = c.client_id
                LEFT JOIN users u ON l.agent_id = u.user_id
                ORDER BY l.created_at DESC
            """
            df = pd.read_sql_query(query, conn)
        
        return df
    
    def get_filtered_invoices(self, conn):
        """
        Get invoices based on user role.
        """
        if self.should_filter_by_agent():
            query = """
                SELECT i.*, c.first_name, c.last_name
                FROM invoices i
                JOIN clients c ON i.client_id = c.client_id
                WHERE c.assigned_agent_id = ? OR i.agent_id = ?
                ORDER BY i.created_at DESC
            """
            df = pd.read_sql_query(query, conn, params=(self.user_id, self.user_id))
        else:
            query = """
                SELECT i.*, c.first_name, c.last_name, u.full_name as agent_name
                FROM invoices i
                JOIN clients c ON i.client_id = c.client_id
                LEFT JOIN users u ON i.agent_id = u.user_id
                ORDER BY i.created_at DESC
            """
            df = pd.read_sql_query(query, conn)
        
        return df
    
    def can_edit_client(self, client_id):
        """
        Check if user can edit a specific client.
        """
        if self.role == 'Admin':
            return True
        
        if self.role == 'agent':
            # Agent can only edit their own clients
            from db_helpers import get_db_connection
            
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT assigned_agent_id FROM clients WHERE client_id = ?",
                    (client_id,)
                )
                result = cursor.fetchone()
                
                if result and result[0] == self.user_id:
                    return True
        
        return False
    
    def can_view_client(self, client_id):
        """
        Check if user can view a specific client.
        """
        if self.role == 'Admin':
            return True
        
        if self.role in ['agent', 'viewer']:
            from db_helpers import get_db_connection
            
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT assigned_agent_id FROM clients WHERE client_id = ?",
                    (client_id,)
                )
                result = cursor.fetchone()
                
                if result and result[0] == self.user_id:
                    return True
        
        return False
    
    def get_dashboard_summary(self, conn):
        """
        Get summary statistics for dashboard based on role.
        """
        if self.should_filter_by_agent():
            # Agent dashboard
            stats = {
                "clients": conn.execute(
                    "SELECT COUNT(*) FROM clients WHERE assigned_agent_id = ?",
                    (self.user_id,)
                ).fetchone()[0],
                "active_loans": conn.execute("""
                    SELECT COUNT(*) FROM loans l
                    JOIN clients c ON l.client_id = c.client_id
                    WHERE c.assigned_agent_id = ? AND l.status = 'Active'
                """, (self.user_id,)).fetchone()[0],
                "pending_invoices": conn.execute("""
                    SELECT COUNT(*) FROM invoices i
                    WHERE (i.agent_id = ? OR (SELECT assigned_agent_id FROM clients WHERE client_id = i.client_id) = ?)
                    AND i.status IN ('Draft', 'Sent')
                """, (self.user_id, self.user_id)).fetchone()[0],
                "overdue_payments": conn.execute("""
                    SELECT COUNT(*) FROM loans l
                    JOIN clients c ON l.client_id = c.client_id
                    WHERE c.assigned_agent_id = ? 
                    AND l.status = 'Overdue'
                """, (self.user_id,)).fetchone()[0],
            }
        else:
            # Admin dashboard
            stats = {
                "total_clients": conn.execute("SELECT COUNT(*) FROM clients").fetchone()[0],
                "active_loans": conn.execute(
                    "SELECT COUNT(*) FROM loans WHERE status = 'Active'"
                ).fetchone()[0],
                "pending_invoices": conn.execute(
                    "SELECT COUNT(*) FROM invoices WHERE status IN ('Draft', 'Sent')"
                ).fetchone()[0],
                "overdue_payments": conn.execute(
                    "SELECT COUNT(*) FROM loans WHERE status = 'Overdue'"
                ).fetchone()[0],
                "total_agents": conn.execute(
                    "SELECT COUNT(*) FROM users WHERE role = 'agent' AND is_active = 1"
                ).fetchone()[0],
            }
        
        return stats


def display_agent_dashboard(dashboard_filter, conn):
    """
    Display a filtered dashboard for an agent.
    Shows only their clients and related data.
    """
    st.subheader("📊 My Dashboard")
    
    stats = dashboard_filter.get_dashboard_summary(conn)
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("My Clients", stats['clients'])
    
    with col2:
        st.metric("Active Loans", stats['active_loans'])
    
    with col3:
        st.metric("Pending Invoices", stats['pending_invoices'])
    
    with col4:
        st.metric("Overdue", stats['overdue_payments'])
    
    st.divider()
    
    # Recent activity for this agent
    tab_clients, tab_loans, tab_invoices = st.tabs(["My Clients", "My Loans", "My Invoices"])
    
    with tab_clients:
        clients = dashboard_filter.get_filtered_clients()
        if clients:
            df = pd.DataFrame(clients)
            display_cols = ['client_id', 'first_name', 'last_name', 'phone', 'status']
            df_display = df[[col for col in display_cols if col in df.columns]].copy()
            df_display.columns = ['ID', 'First Name', 'Last Name', 'Phone', 'Status']
            st.dataframe(df_display, use_container_width=True, hide_index=True)
        else:
            st.info("No clients assigned to you yet.")
    
    with tab_loans:
        loans_df = dashboard_filter.get_filtered_loans(conn)
        if not loans_df.empty:
            display_loans = loans_df[['loan_id', 'first_name', 'last_name', 'principal', 'balance', 'status']].copy()
            display_loans.columns = ['Loan ID', 'First Name', 'Last Name', 'Principal', 'Balance', 'Status']
            st.dataframe(display_loans, use_container_width=True, hide_index=True)
        else:
            st.info("No loans assigned to you yet.")
    
    with tab_invoices:
        invoices_df = dashboard_filter.get_filtered_invoices(conn)
        if not invoices_df.empty:
            display_invoices = invoices_df[['invoice_id', 'first_name', 'last_name', 'amount', 'status']].copy()
            display_invoices.columns = ['Invoice ID', 'First Name', 'Last Name', 'Amount', 'Status']
            st.dataframe(display_invoices, use_container_width=True, hide_index=True)
        else:
            st.info("No invoices generated yet.")


def display_admin_dashboard(dashboard_filter, conn):
    """
    Display the admin dashboard with system-wide overview.
    """
    st.subheader("📊 System Dashboard")
    
    stats = dashboard_filter.get_dashboard_summary(conn)
    
    # Summary metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Clients", stats['total_clients'])
    
    with col2:
        st.metric("Active Loans", stats['active_loans'])
    
    with col3:
        st.metric("Pending Invoices", stats['pending_invoices'])
    
    with col4:
        st.metric("Overdue", stats['overdue_payments'])
    
    with col5:
        st.metric("Active Agents", stats['total_agents'])
    
    st.divider()
    
    # System overview
    tab_overview, tab_agents, tab_alerts = st.tabs(["Overview", "Agent Performance", "Alerts"])
    
    with tab_overview:
        st.write("**System Statistics**")
        # Add detailed admin overview here
        st.info("Admin panel showing system-wide statistics and trends.")
    
    with tab_agents:
        st.write("**Agent Performance Metrics**")
        # Add agent performance data here
        st.info("Agent productivity and performance metrics.")
    
    with tab_alerts:
        st.write("**System Alerts**")
        # Add alerts here
        overdue = conn.execute("SELECT COUNT(*) FROM loans WHERE status = 'Overdue'").fetchone()[0]
        if overdue > 0:
            st.warning(f"⚠️ {overdue} loan(s) are overdue")
