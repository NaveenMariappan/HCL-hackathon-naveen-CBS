from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models import Account, User, KYCApplication
from app.routers.kyc import get_current_user
from app.utils import generate_account_number

router = APIRouter(prefix="/accounts", tags=["Accounts"])

# Request model
class AccountCreateRequest(BaseModel):
    account_type: str  # savings, current, fd
    initial_deposit: int
    email: str | None = None  # Only admin can use this field

# Minimum deposit requirement
MIN_DEPOSIT = {
    "savings": 1000,
    "current": 5000,
    "fd": 10000
}

@router.get("/me")
def get_my_accounts(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    accounts = db.query(Account).filter(Account.user_id == current_user.id).all()
    if not accounts:
        raise HTTPException(status_code=404, detail="No accounts found")
    return accounts

@router.post("/create")
def create_account(request: AccountCreateRequest, db: Session = Depends(get_db), current_user=Depends(get_current_user)):

    # Determine user for account creation
    if current_user.role == "admin" and request.email:
        user = db.query(User).filter(User.email == request.email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
    else:
        user = current_user  # Normal user creating own account

    # Check KYC approval
    kyc = db.query(KYCApplication).filter(KYCApplication.user_id == user.id).first()
    if not kyc or kyc.status != "approved":
        raise HTTPException(status_code=400, detail="KYC not approved. Cannot open account.")

    # Validate account type
    if request.account_type not in MIN_DEPOSIT:
        raise HTTPException(status_code=400, detail="Invalid account type")

    # Check for duplicate account type for same user
    existing_account = db.query(Account).filter(Account.user_id == user.id, Account.account_type == request.account_type).first()
    if existing_account:
        raise HTTPException(status_code=400, detail=f"{request.account_type.capitalize()} account already exists")

    # Validate minimum deposit
    if request.initial_deposit < MIN_DEPOSIT[request.account_type]:
        raise HTTPException(status_code=400, detail=f"Minimum deposit for {request.account_type} is ₹{MIN_DEPOSIT[request.account_type]}")

    # Create account
    account_number = generate_account_number(db)
    new_account = Account(
        user_id=user.id,
        account_number=account_number,
        account_type=request.account_type,
        balance=request.initial_deposit,
        status="active"
    )
    db.add(new_account)
    db.commit()
    db.refresh(new_account)

    return {
        "message": f"{request.account_type.capitalize()} account created successfully",
        "account_number": new_account.account_number,
        "balance": new_account.balance
    }
