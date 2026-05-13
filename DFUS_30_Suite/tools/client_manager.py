"""
Client Management UI for FUS30.
Handles client creation, editing, and agent assignment.
"""
import streamlit as st
import pandas as pd
import sqlite3
from db_helpers import (
    get_active_agents, create_client, get_all_clients, 
    update_client_assignment, get_clients_by_agent
)


def show_agent_assignment_selector(db_path, label="Assign to Agent", default_none=True):
    """
    Display a selectbox for agent assignment.
    
    Args:
        db_path: Path to database
        label: Label for the selectbox
        default_none: Whether to include "Unassigned" option
    
    Returns:
        Selected agent ID or None
    """
    agents = get_active_agents(db_path)
    
    # Build options: (display_name, user_id)
    options = {}
    if default_none:
        options["Unassigned"] = None
    
    for agent in agents:
        display_name = f"{agent['full_name']} ({agent['username']})"
        options[display_name] = agent['user_id']
    
    if not options:
        st.warning("No active agents found. Create an agent first in User Management.")
        return None
    
    selected_display = st.selectbox(label, list(options.keys()))
    return options[selected_display]


def show_add_client_form(db_path):
    """
    Display form to add a new client.
    """
    st.subheader("➕ Add New Client")
    
    with st.form("add_client_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            first_name = st.text_input("First Name", placeholder="John")
            id_number = st.text_input("ID/Passport Number", placeholder="9901015000080")
            phone = st.text_input("Phone Number", placeholder="+27 82 123 4567")
            email = st.text_input("Email (Optional)")
        
        with col2:
            last_name = st.text_input("Last Name", placeholder="Doe")
            employer = st.text_input("Employer (Optional)")
            salary = st.number_input("Annual Salary (Optional)", min_value=0.0)
            address = st.text_area("Physical Address (Optional)", height=50)
        
        st.divider()
        
        # Agent Assignment
        assigned_agent_id = show_agent_assignment_selector(db_path, "Assign to Agent", default_none=True)
        
        submit_btn = st.form_submit_button("✅ Create Client", use_container_width=True)
        
        if submit_btn:
            if not first_name or not last_name or not id_number:
                st.error("First Name, Last Name, and ID Number are required.")
                return False
            
            try:
                client_id = create_client(
                    db_path=db_path,
                    first_name=first_name,
                    last_name=last_name,
                    id_number=id_number,
                    phone=phone,
                    email=email,
                    assigned_agent_id=assigned_agent_id,
                    address=address,
                    salary=salary if salary > 0 else None,
                    employer=employer if employer else None
                )
                
                if client_id:
                    st.success(f"✅ Client '{first_name} {last_name}' created successfully! (ID: {client_id})")
                    return True
                else:
                    st.error("Failed to create client. Check that ID number is unique.")
                    return False
            except Exception as e:
                st.error(f"Error creating client: {e}")
                return False
    
    return False


def show_client_list_with_agent_filter(db_path, current_user_id=None):
    """
    Display list of clients with option to filter by agent.
    If current_user_id is provided, show only their clients by default.
    """
    st.subheader("👥 Client Directory")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        filter_by = st.radio("Filter:", ["All Clients", "My Clients", "Search"], horizontal=True)
    
    with col2:
        if st.button("🔄 Refresh"):
            st.rerun()
    
    # Get data
    if filter_by == "All Clients":
        clients = get_all_clients(db_path)
        st.write(f"**Total Clients:** {len(clients)}")
    
    elif filter_by == "My Clients" and current_user_id:
        clients = get_clients_by_agent(db_path, current_user_id)
        st.write(f"**Your Clients:** {len(clients)}")
    
    else:  # Search
        search_term = st.text_input("Search by name, email, or ID number:")
        if search_term:
            all_clients = get_all_clients(db_path)
            clients = [c for c in all_clients if 
                      search_term.lower() in f"{c['first_name']} {c['last_name']}".lower() or
                      search_term.lower() in str(c.get('email', '')).lower() or
                      search_term.lower() in str(c.get('id_number', '')).lower()]
            st.write(f"**Found:** {len(clients)} client(s)")
        else:
            clients = []
    
    if clients:
        # Display as table
        df = pd.DataFrame(clients)
        display_cols = ['client_id', 'first_name', 'last_name', 'phone', 'agent_name', 'status']
        display_df = df[[col for col in display_cols if col in df.columns]].copy()
        display_df.columns = ['ID', 'First Name', 'Last Name', 'Phone', 'Agent', 'Status']
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.info("No clients found.")


def show_client_detail_view(db_path, client_id, is_admin=False):
    """
    Display detailed view of a single client with edit options.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM clients WHERE client_id = ?", (client_id,))
    client = cursor.fetchone()
    conn.close()
    
    if not client:
        st.error("Client not found.")
        return
    
    client = dict(client)
    
    st.subheader(f"📋 {client['first_name']} {client['last_name']}")
    
    tab_info, tab_edit, tab_agent = st.tabs(["Info", "Edit", "Reassign Agent"])
    
    # TAB 1: INFO
    with tab_info:
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Personal Information**")
            st.write(f"ID Number: {client.get('id_number', 'N/A')}")
            st.write(f"Phone: {client.get('phone', 'N/A')}")
            st.write(f"Email: {client.get('email', 'N/A')}")
            st.write(f"Address: {client.get('address', 'N/A')}")
        
        with col2:
            st.write("**Work Information**")
            st.write(f"Employer: {client.get('employer', 'N/A')}")
            st.write(f"Salary: R{client.get('salary', 0):.2f}")
            st.write(f"Status: {client.get('status', 'Active')}")
        
        st.divider()
        
        # Get loans for this client
        conn = sqlite3.connect(db_path)
        loans_df = pd.read_sql_query(
            "SELECT loan_id, principal, balance, due_date, status FROM loans WHERE client_id = ?",
            conn, params=(client_id,)
        )
        conn.close()
        
        if not loans_df.empty:
            st.write("**Active Loans**")
            st.dataframe(loans_df, use_container_width=True, hide_index=True)
        else:
            st.info("No loans for this client.")
    
    # TAB 2: EDIT
    with tab_edit:
        if is_admin or st.session_state.get('role') == 'Admin':
            with st.form("edit_client_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    new_first = st.text_input("First Name", value=client.get('first_name', ''))
                    new_phone = st.text_input("Phone", value=client.get('phone', ''))
                    new_email = st.text_input("Email", value=client.get('email', ''))
                
                with col2:
                    new_last = st.text_input("Last Name", value=client.get('last_name', ''))
                    new_employer = st.text_input("Employer", value=client.get('employer', ''))
                    new_salary = st.number_input("Salary", value=float(client.get('salary', 0)))
                
                new_address = st.text_area("Address", value=client.get('address', ''))
                
                if st.form_submit_button("💾 Save Changes"):
                    conn = sqlite3.connect(db_path)
                    conn.execute("""
                        UPDATE clients
                        SET first_name=?, last_name=?, phone=?, email=?, 
                            employer=?, salary=?, address=?
                        WHERE client_id=?
                    """, (new_first, new_last, new_phone, new_email, 
                          new_employer, new_salary, new_address, client_id))
                    conn.commit()
                    conn.close()
                    st.success("Client updated successfully!")
                    st.rerun()
        else:
            st.warning("Only administrators can edit client information.")
    
    # TAB 3: REASSIGN AGENT
    with tab_agent:
        if is_admin or st.session_state.get('role') == 'Admin':
            st.write(f"**Current Agent:** {client.get('agent_name', 'Unassigned')}")
            
            new_agent_id = show_agent_assignment_selector(db_path, "Reassign to Agent", default_none=True)
            
            if st.button("🔄 Update Agent Assignment"):
                success = update_client_assignment(db_path, client_id, new_agent_id)
                if success:
                    st.success("Agent assignment updated!")
                    st.rerun()
                else:
                    st.error("Failed to update assignment.")
        else:
            st.warning("Only administrators can reassign agents.")


def run(get_db, db_path, current_user_id=None, is_admin=False):
    """
    Main client management interface.
    """
    st.header("👥 Client Management")
    
    tab_add, tab_view, tab_list = st.tabs(["➕ Add Client", "👤 View Client", "📋 Client List"])
    
    with tab_add:
        show_add_client_form(db_path)
    
    with tab_view:
        client_id = st.number_input("Enter Client ID:", min_value=1)
        if st.button("View Client"):
            show_client_detail_view(db_path, client_id, is_admin=is_admin)
    
    with tab_list:
        show_client_list_with_agent_filter(db_path, current_user_id=current_user_id)
