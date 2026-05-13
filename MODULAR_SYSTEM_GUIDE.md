# FUS30 Modular Invoice Generator - Implementation Guide

## Overview

This modular invoice generator separates concerns into independent components:

1. **Core Data Modules** - Business and client information
2. **Logic & Calculation Engine** - Invoicing and tax calculations
3. **Document & Formatting Module** - Template-based invoice generation
4. **Persistence & Management** - Database layer with audit trails
5. **Distribution Module** - Email and communication (future)

---

## Architecture

### 1. Database Layer (`db_helpers.py`)

**Provides modular access to all database operations.**

#### Key Functions:

```python
# Agent Management
get_active_agents(db_path)                    # List all active agents
get_agent_by_id(db_path, user_id)             # Get specific agent

# Client Management
create_client(db_path, **client_data)         # Create new client
get_clients_by_agent(db_path, agent_id)       # Clients for specific agent
get_all_clients(db_path)                      # All clients (admin only)
update_client_assignment(db_path, client_id, agent_id)  # Reassign

# Invoice Tracking
create_invoice_record(db_path, ...)           # Record invoice
get_next_invoice_number(db_path)              # Generate INV-2026-0001

# Audit Trail
log_invoice_action(db_path, ...)              # Log all actions
```

---

### 2. Business Profile Module (`business_profile.py`)

**Manages company information and calculations.**

#### Classes:

**BusinessProfile**
```python
profile = BusinessProfile(db_path)
profile.get_profile()          # Get all company details
profile.get_vat_rate()         # 15% for ZAR (South Africa)
profile.update_profile({...})  # Update details
```

**InvoiceNumberGenerator**
```python
gen = InvoiceNumberGenerator(db_path)
gen.next_number("INV", year=2026)  # Returns "INV-2026-0001"
```

**TaxCalculator**
```python
calc = TaxCalculator(db_path, currency="ZAR")
totals = calc.calculate_totals(
    line_items=[
        {"quantity": 2, "unit_price": 1000, "description": "Service A"},
        {"quantity": 1, "unit_price": 500, "description": "Service B"}
    ],
    discount=100
)
# Returns:
# {
#     "subtotal": 2500,
#     "discount": 100,
#     "subtotal_after_discount": 2400,
#     "vat": 360,  (2400 * 0.15)
#     "grand_total": 2760,
#     "currency": "ZAR"
# }
```

**InvoiceMetadata**
```python
metadata_gen = InvoiceMetadata(db_path)
metadata = metadata_gen.create_metadata(
    client_id=1,
    agent_id=2,
    due_days=30
)
# Returns metadata with auto-generated invoice number
```

---

### 3. Client Management UI (`client_manager.py`)

**Handles client creation and agent assignment in Streamlit.**

#### Key Functions:

```python
show_agent_assignment_selector(db_path)
# Displays selectbox for agent assignment
# Returns: selected agent_id or None

show_add_client_form(db_path)
# Shows form to create new client with agent assignment

show_client_list_with_agent_filter(db_path, current_user_id)
# Shows clients filtered by role:
# - Admin: All clients
# - Agent: Only their assigned clients

show_client_detail_view(db_path, client_id, is_admin=False)
# Shows detailed client view with edit and reassign options
```

#### Usage in Streamlit App:

```python
from tools.client_manager import run as client_manager_run

db_path = st.session_state.config['db_path']
current_user_id = st.session_state.user_id
is_admin = st.session_state.role == 'Admin'

client_manager_run(get_db, db_path, current_user_id, is_admin)
```

---

### 4. Dashboard Filtering (`dashboard_filter.py`)

**Ensures agents only see their assigned data.**

#### DashboardFilter Class:

```python
from tools.dashboard_filter import DashboardFilter

# Initialize filter
filter = DashboardFilter(
    user_id=st.session_state.user_id,
    role=st.session_state.role,
    db_path=st.session_state.config['db_path']
)

# Get filtered data based on role
clients = filter.get_filtered_clients()
loans = filter.get_filtered_loans(conn)
invoices = filter.get_filtered_invoices(conn)

# Check permissions
if filter.can_edit_client(client_id):
    # Allow edit
    pass

# Get summary stats
stats = filter.get_dashboard_summary(conn)
# Returns: {clients, active_loans, pending_invoices, overdue_payments}
```

#### Usage:

```python
from tools.dashboard_filter import display_agent_dashboard, display_admin_dashboard

if st.session_state.role == 'agent':
    display_agent_dashboard(filter, conn)
else:
    display_admin_dashboard(filter, conn)
```

---

### 5. Database Schema Updates

#### New Columns in `clients` Table:
```sql
assigned_agent_id INTEGER,
FOREIGN KEY(assigned_agent_id) REFERENCES users(user_id)
```

#### New Tables:

**invoices**
```sql
CREATE TABLE invoices (
    invoice_id INTEGER PRIMARY KEY,
    client_id INTEGER,
    agent_id INTEGER,
    invoice_number TEXT UNIQUE,
    amount REAL,
    due_date TEXT,
    status TEXT DEFAULT 'Draft',
    data TEXT,  -- JSON serialized invoice data
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)
```

**invoice_audit**
```sql
CREATE TABLE invoice_audit (
    audit_id INTEGER PRIMARY KEY,
    invoice_id INTEGER,
    agent_id INTEGER,
    action TEXT,  -- 'created', 'sent', 'paid', etc.
    notes TEXT,
    created_at TIMESTAMP
)
```

---

## Workflow: Creating an Invoice

### Step 1: Admin creates client and assigns to agent

```python
from db_helpers import create_client

client_id = create_client(
    db_path="~/path/to/db.sqlite",
    first_name="John",
    last_name="Doe",
    id_number="9901015000080",
    phone="+27 82 123 4567",
    email="john@example.com",
    assigned_agent_id=2,  # Assign to agent with user_id=2
    salary=50000,
    employer="TechCorp"
)
```

### Step 2: Agent generates invoice for their client

```python
from business_profile import (
    InvoiceNumberGenerator, TaxCalculator, InvoiceMetadata
)
from db_helpers import create_invoice_record, log_invoice_action

db_path = "~/path/to/db.sqlite"
agent_id = st.session_state.user_id

# Generate metadata
metadata_gen = InvoiceMetadata(db_path)
metadata = metadata_gen.create_metadata(client_id, agent_id, due_days=30)

# Calculate totals with VAT
calc = TaxCalculator(db_path, "ZAR")
totals = calc.calculate_totals(
    line_items=[
        {"quantity": 1, "unit_price": 5000, "description": "Loan Principal"}
    ],
    discount=0
)

# Create invoice record
invoice_id = create_invoice_record(
    db_path=db_path,
    client_id=client_id,
    agent_id=agent_id,
    invoice_number=metadata['invoice_number'],
    amount=totals['grand_total'],
    due_date=metadata['due_date']
)

# Log action
log_invoice_action(
    db_path=db_path,
    invoice_id=invoice_id,
    action='created',
    agent_id=agent_id,
    notes="Invoice created for client"
)
```

### Step 3: Generate document using template

```python
from tools.invoice_tool import generate_invoice_docx, generate_invoice_pdf

# Get template (or use default)
templates = get_all_templates()
template = templates[0]  # Default

# Generate documents
doc = generate_invoice_docx(loan_data, client_data, payments_data, template)
pdf = generate_invoice_pdf(loan_data, client_data, payments_data, template)

# Save/download
doc_bytes = io.BytesIO()
doc.save(doc_bytes)
```

---

## Role-Based Access Control

### Admin
- **Can:** View all clients, create clients, assign agents, edit any client, view all invoices
- **Dashboard:** System-wide metrics, agent performance

### Agent
- **Can:** View only their assigned clients, create invoices, edit their own clients
- **Dashboard:** Personal metrics, their clients and invoices only
- **Restriction:** Cannot see other agents' clients

### Viewer (Future)
- **Can:** View-only access to assigned clients
- **Cannot:** Edit or create

---

## Multi-Currency & Tax Support

### For South Africa (Default):
```python
# ZAR with 15% VAT
calc = TaxCalculator(db_path, currency="ZAR")
vat_rate = 0.15
```

### For International (Future):
```python
# USD with 10% GST (example)
calc = TaxCalculator(db_path, currency="USD")
# Update business_profile with different rate
```

---

## Error Handling & Audit Trail

### All invoice actions are logged:
```
✅ Invoice Created (INV-2026-0001)
   - Agent: John Smith
   - Client: Jane Doe
   - Amount: R 5,750.00
   - Time: 2026-05-13 10:30:00

✅ Invoice Sent
   - Email sent to: jane@example.com
   - Time: 2026-05-13 11:00:00

✅ Payment Received
   - Amount: R 5,750.00
   - Time: 2026-05-15 14:20:00
```

### Access validation:
```python
filter = DashboardFilter(user_id, role, db_path)

# Before showing client details
if not filter.can_view_client(client_id):
    st.error("You don't have access to this client.")
    st.stop()
```

---

## Key Advantages

✅ **Modularity** - Change PDF library without affecting client management  
✅ **Scalability** - Add new features (WhatsApp, payment gateway) independently  
✅ **Security** - Agents can't access other agents' data  
✅ **Audit Trail** - Every action is logged  
✅ **Multi-Currency Ready** - Easy to extend to other currencies  
✅ **Testing** - Each module can be tested independently  

---

## Next Steps

1. ✅ Database schema updated with `assigned_agent_id`
2. ✅ DB helpers module created
3. ✅ Business profile and calculations module created
4. ✅ Client manager UI created
5. ✅ Dashboard filtering implemented
6. **TODO:** Email integration (SMTP/SendGrid)
7. **TODO:** Payment gateway (PayFast/Stripe)
8. **TODO:** WhatsApp API integration
9. **TODO:** Cloud storage (S3) for PDFs

---

## Quick Reference

| Task | Module | Function |
|------|--------|----------|
| Create client | `db_helpers` | `create_client()` |
| Assign agent | `db_helpers` | `update_client_assignment()` |
| Generate invoice # | `business_profile` | `InvoiceNumberGenerator.next_number()` |
| Calculate tax | `business_profile` | `TaxCalculator.calculate_totals()` |
| Generate PDF | `invoice_tool` | `generate_invoice_pdf()` |
| Generate Word | `invoice_tool` | `generate_invoice_docx()` |
| Filter data for agent | `dashboard_filter` | `DashboardFilter.get_filtered_*()` |
| Log action | `db_helpers` | `log_invoice_action()` |

