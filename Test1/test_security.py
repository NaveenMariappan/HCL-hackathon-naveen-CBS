# tests/test_security.py
from app.security import hash_password, verify_password

def test_hash_verify_roundtrip():
    raw = "Secret@123"
    h = hash_password(raw)
    assert h != raw
    assert verify_password(raw, h)
    assert not verify_password("Wrong@123", h)
