from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from app.database import get_db
from app.models import User, Account, Transaction, KYCApplication
from app.routers.kyc import get_current_user, admin_only

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

IST = timezone(timedelta(hours=5, minutes=30))

def now_ist():
    return datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")

def response(data):
    return {"status": "success", "generated_at": now_ist(), "data": data}

@router.get("/customer/summary")
def customer_summary(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if current_user.role == "admin":
        raise HTTPException(status_code=403, detail="Customers only")
    kyc = db.query(KYCApplication).filter(KYCApplication.user_id == current_user.id).first()
    total_accounts = db.query(func.count(Account.id)).filter(Account.user_id == current_user.id).scalar()
    total_balance = db.query(func.coalesce(func.sum(Account.balance), 0)).filter(Account.user_id == current_user.id).scalar()
    return response({
        "name": current_user.full_name,
        "kyc_status": kyc.status if kyc else "not submitted",
        "total_accounts": total_accounts,
        "total_balance": total_balance
    })

@router.get("/customer/recent-transactions")
def recent_customer_txn(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if current_user.role == "admin":
        raise HTTPException(status_code=403, detail="Customers only")
    accounts = db.query(Account).filter(Account.user_id == current_user.id).all()
    account_numbers = [a.account_number for a in accounts]
    txns = db.query(Transaction).filter(or_(
        Transaction.sender_account.in_(account_numbers),
        Transaction.receiver_account.in_(account_numbers)
    )).order_by(Transaction.timestamp.desc()).limit(5).all()
    return response([{
        "txn_ref": t.reference_id,
        "amount": t.amount,
        "from": t.sender_account,
        "to": t.receiver_account,
        "time": t.timestamp
    } for t in txns])

@router.get("/admin/summary")
def admin_summary(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    admin_only(current_user)
    total_users = db.query(func.count(User.id)).scalar()
    kyc_pending = db.query(func.count(KYCApplication.id)).filter(KYCApplication.status == "pending").scalar()
    kyc_approved = db.query(func.count(KYCApplication.id)).filter(KYCApplication.status == "approved").scalar()
    total_accounts = db.query(func.count(Account.id)).scalar()
    total_balance = db.query(func.coalesce(func.sum(Account.balance), 0)).scalar()
    return response({
        "total_users": total_users,
        "kyc_pending": kyc_pending,
        "kyc_approved": kyc_approved,
        "total_accounts": total_accounts,
        "total_bank_balance": total_balance
    })

@router.get("/admin/recent-transactions")
def admin_recent_txn(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    admin_only(current_user)
    txns = db.query(Transaction).order_by(Transaction.timestamp.desc()).limit(10).all()
    return response([{
        "ref": t.reference_id,
        "from": t.sender_account,
        "to": t.receiver_account,
        "amount": t.amount,
        "time": t.timestamp
    } for t in txns])
