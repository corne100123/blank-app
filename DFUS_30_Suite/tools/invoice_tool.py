import os
import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from fpdf import FPDF

# --- DATABASE CONNECTION ---
def get_local_connection():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "NewLoanManager.db")
    return sqlite3.connect(db_path)

class InvoicePDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'USIZO Loan Invoice', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_loan_invoice(loan_data, client_data, payments_data):
    pdf = InvoicePDF()
    pdf.add_page()
    pdf.set_font('Arial', '', 10)

    # Client Information
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 10, 'Client Information:', 0, 1)
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 10, f'Name: {client_data["first_name"]} {client_data["last_name"]}', 0, 1)
    pdf.cell(0, 10, f'ID Number: {client_data["id_number"]}', 0, 1)
    pdf.cell(0, 10, f'Phone: {client_data["phone"]}', 0, 1)
    pdf.ln(5)

    # Loan Information
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 10, 'Loan Details:', 0, 1)
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 10, f'Loan ID: {loan_data["loan_id"]}', 0, 1)
    pdf.cell(0, 10, f'Principal Amount: R {loan_data["principal"]:.2f}', 0, 1)
    pdf.cell(0, 10, f'Current Balance: R {loan_data["balance"]:.2f}', 0, 1)
    pdf.cell(0, 10, f'Amount Paid: R {loan_data["amount_paid"]:.2f}', 0, 1)
    pdf.cell(0, 10, f'Due Date: {loan_data["due_date"]}', 0, 1)
    pdf.cell(0, 10, f'Status: {loan_data["status"]}', 0, 1)
    pdf.ln(5)

    # Payment History
    if not payments_data.empty:
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(0, 10, 'Payment History:', 0, 1)
        pdf.set_font('Arial', '', 8)
        pdf.cell(30, 10, 'Date', 1)
        pdf.cell(30, 10, 'Amount', 1)
        pdf.cell(30, 10, 'Type', 1)
        pdf.ln()

        for _, payment in payments_data.iterrows():
            pdf.cell(30, 10, payment['date'], 1)
            pdf.cell(30, 10, f'R {payment["amount"]:.2f}', 1)
            pdf.cell(30, 10, payment['type'], 1)
            pdf.ln()

    return pdf

def run(get_db_ignored):
    st.header("📄 Invoice Generator")

    try:
        with get_local_connection() as conn:
            # Get all active loans with client info
            df_loans = pd.read_sql_query("""
                SELECT l.loan_id, l.client_id, l.principal, l.balance, l.amount_paid, l.due_date, l.status,
                       c.first_name, c.last_name, c.id_number, c.phone
                FROM loans l
                JOIN clients c ON l.client_id = c.client_id
                WHERE l.status = 'Active'
            """, conn)

    except Exception as e:
        st.error(f"Database Error: {e}")
        return

    if df_loans.empty:
        st.warning("No active loans found to generate invoices.")
        return

    # Select loan to generate invoice for
    st.subheader("Select Loan for Invoice")
    selected_loan = st.selectbox(
        "Choose a loan:",
        df_loans['loan_id'].tolist(),
        format_func=lambda x: f"Loan {x} - {df_loans[df_loans['loan_id']==x]['first_name'].iloc[0]} {df_loans[df_loans['loan_id']==x]['last_name'].iloc[0]} - R {df_loans[df_loans['loan_id']==x]['balance'].iloc[0]:.2f}"
    )

    if st.button("Generate Invoice"):
        loan_data = df_loans[df_loans['loan_id'] == selected_loan].iloc[0].to_dict()

        # Get payment history for this loan
        with get_local_connection() as conn:
            payments_data = pd.read_sql_query("""
                SELECT date, amount, type
                FROM payment_history
                WHERE loan_id = ?
                ORDER BY date DESC
            """, conn, params=(selected_loan,))

        # Generate PDF
        pdf = generate_loan_invoice(loan_data, loan_data, payments_data)

        # Save to bytes
        pdf_bytes = pdf.output(dest='S').encode('latin1')

        # Download button
        st.download_button(
            label="Download Invoice PDF",
            data=pdf_bytes,
            file_name=f"Loan_Invoice_{selected_loan}_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf"
        )

        st.success("Invoice generated successfully! Click the download button above.")