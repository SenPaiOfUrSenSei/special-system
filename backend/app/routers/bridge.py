from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import datetime
from jose import JWTError, jwt
import time
import random
from typing import List

from app.database import get_db
from app import models, schemas

# JWT Configuration
SECRET_KEY = "bridgr-secure-quantum-ledger-secret-key-hs256-standard"
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

router = APIRouter(prefix="/bridge", tags=["bridge"])

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Session expired or invalid token. Please log in again.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

# Predefined exchange rates relative to USD
RATES = {
    "USDT": 1.0,
    "USDC": 1.0,
    "ETH": 3500.0,
    "SOL": 150.0,
}

@router.get("/balances", response_model=List[schemas.BalanceResponse])
async def get_balances(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    balances = db.query(models.Balance).filter(models.Balance.user_id == current_user.id).all()
    return balances

@router.get("/recipient-currency")
async def get_recipient_currency(recipient: str, db: Session = Depends(get_db)):
    key = recipient.strip().lower()
    user = db.query(models.User).filter(
        (models.User.email == key) | (models.User.username == key)
    ).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipient user not found."
        )
    return {
        "preferred_currency": user.preferred_currency,
        "username": user.username
    }

@router.post("/estimate", response_model=schemas.EstimateResponse)
async def estimate_transaction(request: schemas.EstimateRequest):
    src_rate = RATES.get(request.source_token, 1.0)
    tgt_rate = RATES.get(request.target_token, 1.0)
    
    usd_val = request.amount * src_rate
    l2_fee_usd = (usd_val * 0.0005) + 0.05
    l2_fee_tokens = l2_fee_usd / src_rate
    
    output_amount = (usd_val - l2_fee_usd) / tgt_rate
    if output_amount < 0:
        output_amount = 0.0
        
    l1_gas_saved_usd = random.uniform(15.0, 38.0)
    
    route = [
        f"Verifying Bridgr account balance reserves for {request.amount} {request.source_token}",
        f"Locking transaction parameters into secure L2 rollup pipeline ({request.source_chain})",
        f"Exchanging assets: {request.source_token} -> {request.target_token} via L2 atomic pool",
        f"Delivering {output_amount:.4f} {request.target_token} to recipient on {request.target_chain}"
    ]
    
    return schemas.EstimateResponse(
        source_chain=request.source_chain,
        target_chain=request.target_chain,
        source_token=request.source_token,
        target_token=request.target_token,
        input_amount=request.amount,
        output_amount=round(output_amount, 6),
        l2_fee=round(l2_fee_tokens, 6),
        l1_gas_saved_usd=round(l1_gas_saved_usd, 2),
        estimated_time_sec=3,
        route=route
    )

@router.post("/submit", response_model=schemas.TransferResponse)
async def submit_transaction(
    transfer: schemas.TransferCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # 1. Clean recipient search key (email or username)
    recipient_key = transfer.recipient.strip().lower()
    
    # 2. Find Recipient User
    recipient_user = db.query(models.User).filter(
        (models.User.email == recipient_key) | (models.User.username == recipient_key)
    ).first()
    
    if not recipient_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipient user not found. Please verify their email or username."
        )

    # 3. Check Sender balance in source token
    sender_balance = db.query(models.Balance).filter(
        models.Balance.user_id == current_user.id,
        models.Balance.currency == transfer.source_token
    ).first()
    
    if not sender_balance or sender_balance.amount < transfer.amount:
        available_amt = sender_balance.amount if sender_balance else 0.0
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient balance of {transfer.source_token}. You have {available_amt:.4f} {transfer.source_token} but tried to send {transfer.amount:.4f}."
        )
    
    # 4. Perform exchange conversion into Recipient's Preferred Currency Y
    currency_x = transfer.source_token
    currency_y = recipient_user.preferred_currency
    
    rate_x = RATES.get(currency_x, 1.0)
    rate_y = RATES.get(currency_y, 1.0)
    
    usd_val = transfer.amount * rate_x
    l2_fee_usd = usd_val * 0.0005 # 0.05% fee
    net_usd_val = usd_val - l2_fee_usd
    recipient_credit_amount = net_usd_val / rate_y

    # 5. Deduct from Sender
    sender_balance.amount -= transfer.amount
    
    # 6. Credit Recipient in currency Y
    recipient_balance = db.query(models.Balance).filter(
        models.Balance.user_id == recipient_user.id,
        models.Balance.currency == currency_y
    ).first()
    
    if not recipient_balance:
        # Create balance if not exists
        recipient_balance = models.Balance(
            user_id=recipient_user.id,
            currency=currency_y,
            amount=0.0
        )
        db.add(recipient_balance)
        
    recipient_balance.amount += recipient_credit_amount
    
    # 6.5 Update System Pool tracked balances and exposures
    source_pool = db.query(models.SystemPool).filter(models.SystemPool.currency == currency_x).first()
    if not source_pool:
        source_pool = models.SystemPool(currency=currency_x, tracked_balance=0.0, exposure=0.0)
        db.add(source_pool)
        
    target_pool = db.query(models.SystemPool).filter(models.SystemPool.currency == currency_y).first()
    if not target_pool:
        target_pool = models.SystemPool(currency=currency_y, tracked_balance=0.0, exposure=0.0)
        db.add(target_pool)
        
    source_pool.tracked_balance -= transfer.amount
    source_pool.exposure -= transfer.amount
    
    target_pool.tracked_balance += recipient_credit_amount
    target_pool.exposure += recipient_credit_amount
    
    # Log pool update details to backend console
    print(f"[POOL UPDATE EVENT] Swap transaction submitted: {transfer.amount} {currency_x} -> {recipient_credit_amount} {currency_y}")
    print(f"  Source Pool ({currency_x}): Tracked Balance = {source_pool.tracked_balance:.4f}, Exposure = {source_pool.exposure:.4f}")
    print(f"  Target Pool ({currency_y}): Tracked Balance = {target_pool.tracked_balance:.4f}, Exposure = {target_pool.exposure:.4f}")
    
    # 7. Write to Immutable Ledger
    tx_hash = "0x" + "".join(random.choice("0123456789abcdef") for _ in range(64))
    new_tx = models.Transaction(
        sender_id=current_user.id,
        recipient_id=recipient_user.id,
        source_currency=currency_x,
        target_currency=currency_y,
        source_amount=transfer.amount,
        target_amount=recipient_credit_amount,
        tx_hash=tx_hash,
        status="Completed",
        timestamp=time.time()
    )
    
    db.add(new_tx)
    db.commit()
    db.refresh(new_tx)
    
    return schemas.TransferResponse(
        id=new_tx.id,
        tx_hash=new_tx.tx_hash,
        sender_username=current_user.username,
        recipient_username=recipient_user.username,
        source_currency=new_tx.source_currency,
        target_currency=new_tx.target_currency,
        source_amount=new_tx.source_amount,
        target_amount=new_tx.target_amount,
        status=new_tx.status,
        timestamp=new_tx.timestamp
    )

@router.get("/transactions", response_model=List[schemas.TransferResponse])
async def get_user_transactions(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Fetch transactions where user is sender OR recipient, sorted by recent
    txs = db.query(models.Transaction).filter(
        (models.Transaction.sender_id == current_user.id) | 
        (models.Transaction.recipient_id == current_user.id)
    ).order_by(models.Transaction.timestamp.desc()).all()
    
    mapped_txs = []
    for tx in txs:
        # Fetch usernames
        sender_user = db.query(models.User).filter(models.User.id == tx.sender_id).first()
        recipient_user = db.query(models.User).filter(models.User.id == tx.recipient_id).first()
        
        mapped_txs.append(schemas.TransferResponse(
            id=tx.id,
            tx_hash=tx.tx_hash,
            sender_username=sender_user.username if sender_user else "System Deposit",
            recipient_username=recipient_user.username if recipient_user else "Unknown",
            source_currency=tx.source_currency,
            target_currency=tx.target_currency,
            source_amount=tx.source_amount,
            target_amount=tx.target_amount,
            status=tx.status,
            timestamp=tx.timestamp
        ))
        
    return mapped_txs

@router.get("/pools", response_model=List[schemas.SystemPoolResponse])
async def get_pools(db: Session = Depends(get_db)):
    pools = db.query(models.SystemPool).order_by(models.SystemPool.currency).all()
    return pools

@router.post("/pools/settle/{currency}")
async def settle_pool(
    currency: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    pool = db.query(models.SystemPool).filter(models.SystemPool.currency == currency).first()
    if not pool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"System pool for {currency} not found."
        )
    
    old_exposure = pool.exposure
    pool.exposure = 0.0
    db.commit()
    db.refresh(pool)
    
    # Log settlement details to backend console
    print(f"[SETTLEMENT EVENT] Settle exposure completed for {currency}")
    print(f"  Settled Amount (Exposure Change) = {old_exposure:.4f}")
    print(f"  New Exposure = {pool.exposure:.4f}")
    print(f"  Current Tracked Balance = {pool.tracked_balance:.4f}")
    
    return {
        "currency": pool.currency,
        "tracked_balance": pool.tracked_balance,
        "exposure": pool.exposure,
        "settled_amount": old_exposure
    }

