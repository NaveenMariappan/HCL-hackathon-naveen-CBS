from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.database import get_db
from app.models import Account, Transaction
from app.routers.kyc import get_current_user  # uses your JWT decode
from app.utils import generate_transaction_reference

router = APIRouter(prefix="/transfer", tags=["Transfers"])

# Limits
MIN_TRANSFER = 1            # ₹
MAX_PER_TRANSFER = 50_000   # ₹
DAILY_LIMIT = 200_000       # ₹

class TransferRequest(BaseModel):
    sender_account: str = Field(..., description="Account number of the sender")
    receiver_account: str = Field(..., description="Account number of the receiver")
    amount: int = Field(..., gt=0, description="Amount in rupees (integer)")

def _is_admin(user) -> bool:
    return getattr(user, "role", "") == "admin"

def _today_range_utc():
    # naive UTC window
    now = datetime.utcnow()
    start = datetime(now.year, now.month, now.day)
    end = start + timedelta(days=1)
    return start, end

@router.post("", summary="Internal transfer between accounts")
def make_transfer(req: TransferRequest, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    if req.sender_account == req.receiver_account:
        raise HTTPException(status_code=400, detail="Cannot transfer to the same account")

    # Load accounts
    sender = db.query(Account).filter(Account.account_number == req.sender_account).first()
    if not sender:
        raise HTTPException(status_code=404, detail="Sender account not found")

    receiver = db.query(Account).filter(Account.account_number == req.receiver_account).first()
    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver account not found")

    # Status checks
    if sender.status != "active":
        raise HTTPException(status_code=400, detail="Sender account is not active")
    if receiver.status != "active":
        raise HTTPException(status_code=400, detail="Receiver account is not active")

    # Ownership: users can only send from their own account; admin can send from any
    if not _is_admin(current_user) and sender.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You are not allowed to transfer from this account")

    # Amount rules
    if req.amount < MIN_TRANSFER:
        raise HTTPException(status_code=400, detail=f"Minimum transfer is ₹{MIN_TRANSFER}")
    if req.amount > MAX_PER_TRANSFER:
        raise HTTPException(status_code=400, detail=f"Maximum per transfer is ₹{MAX_PER_TRANSFER}")

    # Daily limit: compute all successful debits from this sender today
    start, end = _today_range_utc()
    todays_total = (
        db.query(func.coalesce(func.sum(Transaction.amount), 0))
          .filter(
              Transaction.sender_account == sender.account_number,
              Transaction.timestamp >= start,
              Transaction.timestamp < end,
              Transaction.status == "success",
          ).scalar()
    )
    if todays_total + req.amount > DAILY_LIMIT:
        raise HTTPException(status_code=400, detail="Daily transfer limit exceeded")

    # Balance check
    if sender.balance < req.amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")

    # Atomic transfer
    try:
            # Update balances
            sender.balance = sender.balance - req.amount
            receiver.balance = receiver.balance + req.amount

            # Create transaction record (only for success, per your choice)
            ref = generate_transaction_reference()
            txn = Transaction(
                sender_account=sender.account_number,
                receiver_account=receiver.account_number,
                amount=req.amount,
                status="success",
                reference_id=ref,
            )
            db.add(txn)
    except Exception as e:
            raise HTTPException(status_code=500, detail=f"Transfer failed: {str(e)}")


    return {
        "message": "Transfer successful",
        "reference_id": ref,
        "debited_from": sender.account_number,
        "credited_to": receiver.account_number,
        "amount": req.amount
    }
