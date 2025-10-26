# frontend/customer.py
import streamlit as st
from utils import require_auth, file_is_allowed
import api

def page_dashboard():
    if not require_auth("customer"): return
    st.subheader("Customer Dashboard")
    s = api.customer_summary(st.session_state["token"])
    if s.ok:
        data = s.json()["data"]
        st.metric("KYC Status", data["kyc_status"])
        st.metric("Total Accounts", data["total_accounts"])
        st.metric("Total Balance (₹)", data["total_balance"])
    else:
        st.error(s.text)

        st.write("### Recent Transactions")
    rt = api.customer_recent_txns(st.session_state["token"])
    if rt.ok:
        data = rt.json().get("data", {})
        txns = data if isinstance(data, list) else data.get("recent_transactions", [])
        if not txns:
            st.info("No recent transactions.")
        else:
            for t in txns:
                st.write(f'**{t.get("timestamp","")}** — {t.get("type","").upper()} ₹{t.get("amount","")} (ref {t.get("reference_id","")})')
    else:
        st.info("No transactions yet.")

def page_kyc():
    if not require_auth("customer"): return
    st.subheader("KYC")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Create/Check KYC Application"):
            r = api.kyc_apply(st.session_state["token"])
            if r.ok:
                st.success(r.json().get("message", "OK"))
                st.json(r.json())
            else:
                st.error(r.text)

        ks = api.kyc_status(st.session_state["token"])
        if ks.ok:
            st.write("**Current Status:**", ks.json().get("status"))
            st.write("**KYC ID:**", ks.json().get("kyc_id"))
        else:
            st.warning("No KYC record yet. Click the button on the left.")

    st.write("---")
    st.write("### Upload Documents (PDF/JPG/PNG)")
    ks = api.kyc_status(st.session_state["token"])
    if not ks.ok:
        st.info("Create KYC application first.")
        return
    kyc_id = ks.json()["kyc_id"]

    doc_type = st.selectbox("Document Type", ["aadhaar", "pan", "selfie"])
    up = st.file_uploader("Choose a file", type=["pdf", "jpg", "jpeg", "png"])
    if up and st.button("Upload"):
        ok, mime = file_is_allowed(up.name)
        if not ok:
            st.error("Only PDF/JPG/PNG allowed.")
            return
        file_tuple = (up.name, up.read(), mime)
        r = api.kyc_upload(st.session_state["token"], kyc_id, doc_type, file_tuple)
        if r.ok:
            st.success(f"{doc_type.capitalize()} uploaded.")
        else:
            st.error(r.text)

def page_accounts():
    if not require_auth("customer"): return
    st.subheader("My Accounts")
    r = api.my_accounts(st.session_state["token"])
    if r.ok:
        for a in r.json():
            st.write(f'**{a["account_type"].upper()}** — **{a["account_number"]}** — ₹{a["balance"]} — {a["status"]}')
    else:
        st.error(r.text)

    st.write("---")
    st.write("### Open New Account")
    acct_type = st.selectbox("Account Type", ["savings", "current", "fd"])
    initial = st.number_input("Initial Deposit (₹)", min_value=0, value=1000, step=500)
    if st.button("Create Account"):
        r2 = api.create_account(st.session_state["token"], acct_type, int(initial))
        if r2.ok:
            st.success(r2.json()["message"])
            st.json(r2.json())
        else:
            st.error(r2.text)

def page_transfer():
    if not require_auth("customer"): return
    st.subheader("Transfer Money (Internal)")
    my = api.my_accounts(st.session_state["token"])
    my_list = []
    if my.ok:
        my_list = [a["account_number"] for a in my.json()]

    sender = st.selectbox("Your Account (Debit)", my_list)
    receiver = st.text_input("Receiver Account Number")
    amount = st.number_input("Amount (₹)", min_value=1, value=1000, step=100)
    if st.button("Send"):
        r = api.transfer(st.session_state["token"], sender, receiver, int(amount))
        if r.ok:
            st.success("Transfer successful.")
            st.json(r.json())
        else:
            st.error(r.text)

def page_transactions():
    if not require_auth("customer"): return
    st.subheader("My Transactions")
    r = api.my_transactions(st.session_state["token"])
    if r.ok:
        for t in r.json():
            st.write(f'[{t["timestamp"]}] {t["reference_id"]} — ₹{t["amount"]} — {t["sender_account"]} → {t["receiver_account"]}')
    else:
        st.error(r.text)
