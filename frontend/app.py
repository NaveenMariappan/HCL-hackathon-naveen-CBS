# frontend/app.py
import streamlit as st
import api
from utils import init_state, navbar, logout
import customer
import admin as admin_pages

st.set_page_config(page_title="Core Banking UI", page_icon="🏦", layout="centered")

init_state()

st.title("🏦 Core Banking System — Demo UI (Light Mode)")

# Top navbar
tabs = ["Login", "Register", "Customer", "Admin", "Logout"]
active = navbar(tabs)

# ---------- Login ----------
if active == "Login":
    st.subheader("Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        res = api.login(email, password)
        if res.ok:
            token = res.json().get("access_token")
            if not token:
                st.error("No token returned.")
            else:
                st.session_state["token"] = token
                # quick role check by trying customer summary; if forbidden, try admin summary
                cs = api.customer_summary(token)
                if cs.status_code == 200:
                    st.session_state["role"] = "customer"
                    st.session_state["email"] = email
                    st.session_state["full_name"] = email.split("@")[0].title()
                    st.success("Logged in as Customer.")
                    st.session_state["active_tab"] = "Customer"
                else:
                    asu = api.admin_summary(token)
                    if asu.status_code == 200:
                        st.session_state["role"] = "admin"
                        st.session_state["email"] = email
                        st.session_state["full_name"] = "Admin"
                        st.success("Logged in as Admin.")
                        st.session_state["active_tab"] = "Admin"
                    else:
                        st.warning("Login succeeded, but role detection failed. Using Customer by default.")
                        st.session_state["role"] = "customer"
                        st.session_state["active_tab"] = "Customer"
        else:
            st.error(res.text)

# ---------- Register ----------
elif active == "Register":
    st.subheader("Register (Customer)")
    full_name = st.text_input("Full Name")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Create Account"):
        r = api.register(email, password, full_name)
        if r.ok:
            st.success("Registered successfully. Please login.")
            st.session_state["active_tab"] = "Login"
        else:
            st.error(r.text)

# ---------- Customer ----------
elif active == "Customer":
    if st.session_state["role"] != "customer":
        st.info("Please login as Customer.")
    else:
        st.write(f"Hello, **{st.session_state.get('full_name','Customer')}**")
        sec = st.selectbox("Section", ["Dashboard", "KYC", "Accounts", "Transfer", "Transactions"])
        if sec == "Dashboard":
            customer.page_dashboard()
        elif sec == "KYC":
            customer.page_kyc()
        elif sec == "Accounts":
            customer.page_accounts()
        elif sec == "Transfer":
            customer.page_transfer()
        elif sec == "Transactions":
            customer.page_transactions()

# ---------- Admin ----------
elif active == "Admin":
    if st.session_state["role"] != "admin":
        st.info("Please login as Admin.")
    else:
        st.write(f"Welcome, **Admin**")
        sec = st.selectbox("Section", ["Dashboard", "KYC Review", "Open Account"])
        if sec == "Dashboard":
            admin_pages.page_admin_dashboard()
        elif sec == "KYC Review":
            admin_pages.page_admin_kyc()
        elif sec == "Open Account":
            admin_pages.page_admin_accounts()

# ---------- Logout ----------
elif active == "Logout":
    logout()
    st.success("Logged out.")
    st.session_state["active_tab"] = "Login"
