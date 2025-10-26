# tests/test_flow_transfer.py
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import KYCApplication

def _register(client: TestClient, email: str, password: str, full_name: str="Test"):
    return client.post("/auth/register", json={"email": email, "password": password, "full_name": full_name})

def _login(client: TestClient, email: str, password: str) -> str:
    r = client.post("/auth/login", data={"username": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]

def _headers(tok: str): return {"Authorization": f"Bearer {tok}"}

def _approve_kyc_direct(client: TestClient):
    # flip all KYC applications in DB to approved (shortcut for tests)
    gen = get_db()
    db: Session = next(gen)
    try:
        rows = db.query(KYCApplication).filter(KYCApplication.status != "approved").all()
        for row in rows:
            row.status = "approved"
        db.commit()
    finally:
        try:
            next(gen)
        except StopIteration:
            pass

def test_register_login_transfer_flow(client: TestClient):
    # register two users (ignore 400 if rerun)
    _register(client, "u1@test.com", "Test@123", "U1")
    _register(client, "u2@test.com", "Test@123", "U2")

    # login both
    tok1 = _login(client, "u1@test.com", "Test@123")
    tok2 = _login(client, "u2@test.com", "Test@123")

    # each applies for KYC
    client.post("/kyc/apply", headers=_headers(tok1))
    client.post("/kyc/apply", headers=_headers(tok2))

    # approve in DB (test shortcut)
    _approve_kyc_direct(client)

    # create accounts
    a1 = client.post("/accounts/create", headers=_headers(tok1),
                     json={"account_type":"savings","initial_deposit":5000})
    assert a1.status_code == 200, a1.text
    acct1 = a1.json()["account_number"]

    a2 = client.post("/accounts/create", headers=_headers(tok2),
                     json={"account_type":"savings","initial_deposit":1000})
    assert a2.status_code == 200, a2.text
    acct2 = a2.json()["account_number"]

    # transfer from u1 to u2
    t = client.post("/transfer", headers=_headers(tok1),
                    json={"sender_account": acct1, "receiver_account": acct2, "amount": 500})
    assert t.status_code == 200, t.text
    assert t.json()["message"] == "Transfer successful"
