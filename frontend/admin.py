# frontend/admin.py
import streamlit as st
from utils import require_auth
import api
import requests

def page_admin_dashboard():
    if not require_auth("admin"): return
    st.subheader("Admin Dashboard")
    s = api.admin_summary(st.session_state["token"])
    if s.ok:
        data = s.json()["data"]
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Total Users", data["total_users"])
        c2.metric("KYC Pending", data["kyc_pending"])
        c3.metric("KYC Approved", data["kyc_approved"])
        c4.metric("Total Accounts", data["total_accounts"])
        c5.metric("Bank Balance (₹)", data["total_bank_balance"])
    else:
        st.error(s.text)

    st.write("### Recent Transactions")
    rt = api.admin_recent_txns(st.session_state["token"])
    if rt.ok:
        for t in rt.json()["data"]:
            st.write(f'[{t["time"]}] {t["ref"]} — ₹{t["amount"]} — {t["from"]} → {t["to"]}')
    else:
        st.info("No transactions yet.")

def page_admin_kyc():
    if not require_auth("admin"): return
    st.subheader("KYC Review (Pending)")
    # endpoint from your kyc router: /kyc/admin/pending and /kyc/admin/{kyc_id}/verify
    # We'll call them via requests directly since api.py doesn't include these two.
    headers = {"Authorization": f"Bearer {st.session_state['token']}"}
    pending = requests.get("http://127.0.0.1:8000/kyc/admin/pending", headers=headers)
    if pending.ok:
        data = pending.json().get("data") or pending.json()  # handle both shapes
        if isinstance(data, dict) and "data" in data:
            kycs = data["data"]
        else:
            kycs = data if isinstance(data, list) else pending.json()
        if not kycs:
            st.info("No pending KYC.")
        for k in kycs:
            st.write(f'KYC ID: {k["id"]}  |  user_id: {k["user_id"]}  |  status: {k["status"]}')
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"Approve #{k['id']}", key=f"ap{k['id']}"):
                    r = requests.put(f"http://127.0.0.1:8000/kyc/admin/{k['id']}/verify",
                                     params={"decision": "approved"}, headers=headers)
                    st.write(r.text if not r.ok else "Approved ✓")
            with col2:
                if st.button(f"Reject #{k['id']}", key=f"rj{k['id']}"):
                    r = requests.put(f"http://127.0.0.1:8000/kyc/admin/{k['id']}/verify",
                                     params={"decision": "rejected"}, headers=headers)
                    st.write(r.text if not r.ok else "Rejected ✗")
    else:
        st.error(pending.text)

def page_admin_accounts():
    if not require_auth("admin"): return
    st.subheader("Open Account For User")
    email = st.text_input("Customer Email")
    acct_type = st.selectbox("Account Type", ["savings", "current", "fd"])
    initial = st.number_input("Initial Deposit (₹)", min_value=0, value=1000, step=500)
    if st.button("Create Account"):
        r = api.create_account(st.session_state["token"], acct_type, int(initial), email=email)
        if r.ok:
            st.success(r.json()["message"])
            st.json(r.json())
        else:
            st.error(r.text)
