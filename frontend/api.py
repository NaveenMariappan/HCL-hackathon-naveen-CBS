import requests

BASE_URL = "http://127.0.0.1:8000"

def _auth_header(token: str | None):
    return {"Authorization": f"Bearer {token}"} if token else {}

# ---------- Auth ----------
def register(email: str, password: str, full_name: str):
    return requests.post(f"{BASE_URL}/auth/register", json={
        "email": email, "password": password, "full_name": full_name
    })

def create_admin(email: str, password: str, full_name: str = "Admin"):
    return requests.post(f"{BASE_URL}/auth/create-admin", json={
        "email": email, "password": password, "full_name": full_name
    })

def login(email: str, password: str):
    # OAuth2 form (username/password)
    data = {"username": email, "password": password}
    return requests.post(f"{BASE_URL}/auth/login", data=data)

# ---------- Dashboard ----------
def customer_summary(token: str):
    return requests.get(f"{BASE_URL}/dashboard/customer/summary",
                        headers=_auth_header(token))

def customer_recent_txns(token: str):
    return requests.get(f"{BASE_URL}/dashboard/customer/recent-transactions",
                        headers=_auth_header(token))

def admin_summary(token: str):
    return requests.get(f"{BASE_URL}/dashboard/admin/summary",
                        headers=_auth_header(token))

def admin_recent_txns(token: str):
    return requests.get(f"{BASE_URL}/dashboard/admin/recent-transactions",
                        headers=_auth_header(token))

# ---------- KYC ----------
def kyc_apply(token: str):
    return requests.post(f"{BASE_URL}/kyc/apply", headers=_auth_header(token))

def kyc_status(token: str):
    return requests.get(f"{BASE_URL}/kyc/status", headers=_auth_header(token))

def kyc_upload(token: str, kyc_id: int, document_type: str, file_tuple):
    # file_tuple: ("filename.ext", bytes, "mime/type")
    files = {"file": file_tuple}
    params = {"document_type": document_type}
    return requests.post(f"{BASE_URL}/kyc/{kyc_id}/upload",
                         headers=_auth_header(token),
                         files=files, params=params)

# ---------- Accounts ----------
def my_accounts(token: str):
    return requests.get(f"{BASE_URL}/accounts/me", headers=_auth_header(token))

def create_account(token: str, account_type: str, initial_deposit: int, email: str | None = None):
    body = {"account_type": account_type, "initial_deposit": initial_deposit}
    if email: body["email"] = email
    return requests.post(f"{BASE_URL}/accounts/create", json=body, headers=_auth_header(token))

# ---------- Transfers & Transactions ----------
def transfer(token: str, sender_acct: str, receiver_acct: str, amount: int):
    body = {"sender_account": sender_acct, "receiver_account": receiver_acct, "amount": amount}
    return requests.post(f"{BASE_URL}/transfer", json=body, headers=_auth_header(token))

def my_transactions(token: str):
    return requests.get(f"{BASE_URL}/transactions/me", headers=_auth_header(token))

def all_transactions(token: str):
    return requests.get(f"{BASE_URL}/transactions/all", headers=_auth_header(token))
