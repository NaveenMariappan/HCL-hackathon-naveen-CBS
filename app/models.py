from sqlalchemy import Column, Integer, String
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, default="customer")  # default role customer
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

class KYCApplication(Base):
    __tablename__ = "kyc_applications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String, default="pending")  # pending, approved, rejected
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")


class KYCDocument(Base):
    __tablename__ = "kyc_documents"

    id = Column(Integer, primary_key=True, index=True)
    kyc_id = Column(Integer, ForeignKey("kyc_applications.id"))
    document_type = Column(String)  # aadhaar, pan, selfie
    file_path = Column(String)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    kyc_application = relationship("KYCApplication")

class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    account_number = Column(String, unique=True, index=True)
    account_type = Column(String, default="savings")  # savings, current
    balance = Column(Integer, default=0)  # initial balance 0
    status = Column(String, default="active")  # active, frozen, closed

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from datetime import datetime

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    sender_account = Column(String, nullable=False)
    receiver_account = Column(String, nullable=False)
    amount = Column(Integer, nullable=False)
    status = Column(String, default="success")  # success, failed
    timestamp = Column(DateTime, default=datetime.utcnow)
    reference_id = Column(String, unique=True, index=True)
