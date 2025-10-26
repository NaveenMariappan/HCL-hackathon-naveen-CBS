from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.database import get_db
from app.models import Account, Transaction
from app.routers.kyc import get_current_user, admin_only

router = APIRouter(prefix="/transactions", tags=["Transactions"])

@router.get("/me")
def get_my_transactions(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    accounts = db.query(Account).filter(Account.user_id == current_user.id).all()
    if not accounts:
        raise HTTPException(status_code=404, detail="No accounts found")

    account_nums = [acc.account_number for acc in accounts]
    txns = db.query(Transaction).filter(
        or_(
            Transaction.sender_account.in_(account_nums),
            Transaction.receiver_account.in_(account_nums)
        )
    ).order_by(Transaction.timestamp.desc()).all()

    return txns

@router.get("/all")
def get_all_transactions(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    admin_only(current_user)
    return db.query(Transaction).order_by(Transaction.timestamp.desc()).all()
