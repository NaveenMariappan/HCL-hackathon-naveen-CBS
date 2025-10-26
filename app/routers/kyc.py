from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
import os
from app.security import SECRET_KEY, ALGORITHM
from app.utils import generate_account_number  

router = APIRouter(prefix="/kyc", tags=["KYC"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Utility – get current user
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        user = db.query(models.User).filter(models.User.email == email).first()
        if not user:
            raise HTTPException(status_code=401, detail="Invalid user")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
def admin_only(user):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access only")

# 1. Create KYC Application
@router.post("/apply")
def create_kyc_application(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    existing_kyc = db.query(models.KYCApplication).filter(models.KYCApplication.user_id == current_user.id).first()
    if existing_kyc:
        return {"message": "KYC application already exists", "kyc_id": existing_kyc.id}

    new_kyc = models.KYCApplication(user_id=current_user.id)
    db.add(new_kyc)
    db.commit()
    db.refresh(new_kyc)
    return {"message": "KYC application created", "kyc_id": new_kyc.id}

# 2. Upload KYC Documents
@router.post("/{kyc_id}/upload")
def upload_kyc_document(
    kyc_id: int,
    document_type: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    allowed_docs = ["aadhaar", "pan", "selfie"]
    if document_type not in allowed_docs:
        raise HTTPException(status_code=400, detail="Invalid document type")

    kyc = db.query(models.KYCApplication).filter(models.KYCApplication.id == kyc_id).first()
    if not kyc or kyc.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="KYC application not found or access denied")

    save_dir = f"storage/kyc/{current_user.id}/{document_type}"
    os.makedirs(save_dir, exist_ok=True)
    file_path = f"{save_dir}/{file.filename}"

    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())

    new_doc = models.KYCDocument(kyc_id=kyc_id, document_type=document_type, file_path=file_path)
    db.add(new_doc)
    db.commit()

    return {"message": f"{document_type} uploaded successfully"}

# 3. View KYC Status
@router.get("/status")
def get_kyc_status(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    kyc = db.query(models.KYCApplication).filter(models.KYCApplication.user_id == current_user.id).first()
    if not kyc:
        raise HTTPException(status_code=404, detail="No KYC application found")
    return {"kyc_id": kyc.id, "status": kyc.status}
# ---------------- Admin KYC Review ----------------

# 4. Admin - View pending KYC requests
@router.get("/admin/pending")
def get_pending_kyc(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    # Allow only admin
    admin_only(current_user)

    pending_kyc = db.query(models.KYCApplication).filter(models.KYCApplication.status == "pending").all()
    return {
        "message": "Pending KYC applications",
        "count": len(pending_kyc),
        "data": pending_kyc
    }

# 5. Admin - Approve / Reject KYC
@router.put("/admin/{kyc_id}/verify")
def verify_kyc(kyc_id: int, decision: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    # Only admin can approve/reject
    admin_only(current_user)

    if decision not in ["approved", "rejected"]:
        raise HTTPException(status_code=400, detail="Invalid decision. Use 'approved' or 'rejected'.")

    kyc = db.query(models.KYCApplication).filter(models.KYCApplication.id == kyc_id).first()
    if not kyc:
        raise HTTPException(status_code=404, detail="KYC application not found")

    kyc.status = decision
    db.commit()

    # ✅ If approved, create account automatically
    if decision == "approved":
        existing_account = db.query(models.Account).filter(models.Account.user_id == kyc.user_id).first()
        if not existing_account:
            account_number = generate_account_number(db)
            new_account = models.Account(
                user_id=kyc.user_id,
                account_number=account_number,
                account_type="savings",
                balance=0
            )
            db.add(new_account)
            db.commit()
            return {"message": "KYC approved and account created", "account_number": account_number}

    return {"message": f"KYC has been {decision} successfully"}