import uuid
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class UserBase(BaseModel):
    email: str
    username: str
    first_name: str
    last_name: str
    preferred_currency: str = "USDT"

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    username_or_email: str
    password: str

class UserResponse(UserBase):
    id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True

class BalanceResponse(BaseModel):
    currency: str
    amount: float

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user_email: str
    username: str
    first_name: str
    preferred_currency: str

class TokenData(BaseModel):
    email_or_username: Optional[str] = None

class EstimateRequest(BaseModel):
    source_chain: str
    target_chain: str
    source_token: str
    target_token: str
    amount: float

class EstimateResponse(BaseModel):
    source_chain: str
    target_chain: str
    source_token: str
    target_token: str
    input_amount: float
    output_amount: float
    l2_fee: float
    l1_gas_saved_usd: float
    estimated_time_sec: int
    route: List[str]

class TransferCreate(BaseModel):
    source_chain: str
    target_chain: str
    source_token: str
    target_token: str
    amount: float
    recipient: str

class TransferResponse(BaseModel):
    id: uuid.UUID
    tx_hash: Optional[str]
    sender_username: Optional[str]
    recipient_username: str
    source_currency: str
    target_currency: str
    source_amount: float
    target_amount: float
    status: str
    timestamp: float

    class Config:
        from_attributes = True

class SystemPoolResponse(BaseModel):
    currency: str
    tracked_balance: float
    exposure: float

    class Config:
        from_attributes = True


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]

