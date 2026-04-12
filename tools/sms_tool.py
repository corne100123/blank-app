import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

def run(get_db):
    st.title("📱 SMS Collection Hub")
    st.write("Send payment reminders to clients with upcoming due dates.")

    # 1. IDENTIFY UPCOMING PAYMENTS (Next 3 Days)
    today = datetime.now().date()
    three_days_time = today + timedelta(days=3)

    with get_db() as conn:
        query = f"""
            SELECT l.loan_id, c.surname, c.phone_cell, l.balance, l.due_date 
            FROM loans l 
            JOIN clients c ON l.client_id = c.client_id 
            WHERE l.status = 'Active' 
            AND l.due_date <= '{three_days_time.strftime('%Y-%m-%d')}'
        """
        upcoming = pd.read_sql_query(query, conn)

    if upcoming.empty:
        st.info("✅ All collections are up to date. No reminders needed for the next 3 days.")
        return

    st.subheader(f"📢 Pending Reminders ({len(upcoming)})")
    
    # 2. BULK SELECTION UI
    for idx, row in upcoming.iterrows():
        with st.container():
            col1, col2, col3 = st.columns([2, 2, 3])
            
            # Formatting the date for the message
            due = datetime.strptime(row['due_date'], "%Y-%m-%d").strftime("%d %b")
            
            col1.write(f"**{row['surname']}**")
            col2.write(f"R {row['balance']:.2f} (Due: {due})")
            
            # The Message Template
            msg = f"Hi {row['surname']}, reminder from USIZO: Your payment of R{row['balance']:.2f} is due by {due}. Ref: {row['loan_id']}. Please pay to avoid penalties."
            
            edited_msg = col3.text_area("Edit Message", value=msg, key=f"msg_{idx}", height=70)
            
            if st.button(f"📤 Send to {row['phone_cell']}", key=f"btn_{idx}"):
                # --- GATEWAY LOGIC ---
                # This is where we link to your SMS Provider
                # Example: requests.post(SMS_API_URL, data={'to': row['phone_cell'], 'message': edited_msg})
                st.success(f"SMS Sent to {row['surname']} at {row['phone_cell']}!")

    # 3. BULK ACTION
    st.markdown("---")
    if st.button("🚀 Send All Reminders (Bulk)"):
        st.warning("Bulk sending initiated... (Integrating with SMS Gateway)")
        # Loop through 'upcoming' and fire the API for each row