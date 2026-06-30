import datetime
import random
import uuid
import time
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Date, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

def generate_unique_mobile():
    # Return a unique 10-digit numeric string based on time
    time.sleep(0.002) # ensure uniqueness
    return str(int(time.time() * 1000))[-10:]

def generate_unique_pan():
    # Return a unique PAN string (5 letters, 4 digits, 1 letter)
    time.sleep(0.002)
    random_letters = "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=5))
    random_digits = "".join(random.choices("0123456789", k=4))
    last_letter = random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    return f"{random_letters}{random_digits}{last_letter}"

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    preferred_currency = Column(String, nullable=False, default="USDT")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Pre-existing fields in PostgreSQL schema
    dob = Column(Date, nullable=False, default=datetime.date(2000, 1, 1))
    mobile = Column(String, unique=True, index=True, nullable=False, default=generate_unique_mobile)
    pan = Column(String, unique=True, nullable=False, default=generate_unique_pan)
    tc_accepted = Column(Boolean, nullable=False, default=True)

    balances = relationship("Balance", back_populates="owner", cascade="all, delete-orphan")
    transactions_sent = relationship("Transaction", back_populates="sender", foreign_keys="[Transaction.sender_id]")
    transactions_received = relationship("Transaction", back_populates="recipient", foreign_keys="[Transaction.recipient_id]")

class Balance(Base):
    __tablename__ = "balances"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    currency = Column(String, index=True, nullable=False)
    amount = Column(Float, nullable=False, default=0.0)

    owner = relationship("User", back_populates="balances")

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Pre-existing fields in PostgreSQL transactions table
    fetch_session_id = Column(UUID(as_uuid=True), nullable=False, default=uuid.UUID('979dbe10-4972-4fa0-9c88-9b9a39710000'))
    payment_ref_id = Column(String, nullable=True)
    amount = Column(Integer, nullable=False, default=0)
    payment_gateway = Column(String, nullable=False, default="Bridgr L2 Engine")
    status = Column(String, nullable=False, default="Completed")
    created_at = Column(DateTime, nullable=True, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True, default=datetime.datetime.utcnow)
    customer_name = Column(String, nullable=False, default="Bridgr User")
    bill_number = Column(String, nullable=False, default="BRIDGR-TX")

    # Our fields
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    recipient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    source_currency = Column(String, nullable=True)
    target_currency = Column(String, nullable=True)
    source_amount = Column(Float, nullable=True)
    target_amount = Column(Float, nullable=True)
    tx_hash = Column(String, unique=True, index=True, nullable=True)
    timestamp = Column(Float, nullable=True)

    sender = relationship("User", back_populates="transactions_sent", foreign_keys=[sender_id])
    recipient = relationship("User", back_populates="transactions_received", foreign_keys=[recipient_id])

class SystemPool(Base):
    __tablename__ = "system_pools"

    id = Column(Integer, primary_key=True, index=True)
    currency = Column(String, unique=True, index=True, nullable=False)
    tracked_balance = Column(Float, nullable=False, default=0.0)
    exposure = Column(Float, nullable=False, default=0.0)

