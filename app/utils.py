from datetime import datetime
from sqlalchemy.orm import Session
from app.models import Account
import random
import string

def generate_account_number(db: Session):
    year = datetime.now().year
    last_account = db.query(Account).order_by(Account.id.desc()).first()
    if last_account:
        seq = last_account.id + 1
    else:
        seq = 1
    return f"{year}{seq:06d}"  # Example: 2025000001

def generate_transaction_reference():
    return "TXN" + ''.join(random.choices(string.digits, k=9))
