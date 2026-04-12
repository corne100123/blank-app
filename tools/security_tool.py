import streamlit as st
import hashlib
import pandas as pd

def run(get_db):
    st.header("👥 User Admin")
    if st.session_state.role != "Admin": st.error("Admin Only"); return
    
    with st.form("new_u"):
        nu = st.text_input("Username")
        np = st.text_input("Password", type="password")
        if st.form_submit_button("Add User"):
            hp = hashlib.sha256(np.encode()).hexdigest()
            with get_db() as conn:
                conn.execute("INSERT INTO users (username, password, role) VALUES (?,?,'Staff')", (nu, hp))
                conn.commit(); st.success("Added")