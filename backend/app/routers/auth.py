from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from jose import jwt
import bcrypt

from app.database import get_db
from app import models, schemas

# JWT Configuration
SECRET_KEY = "bridgr-secure-quantum-ledger-secret-key-hs256-standard"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 7 Days

router = APIRouter(prefix="/auth", tags=["auth"])

def get_password_hash(password: str) -> str:
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    plain_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(plain_bytes, hashed_bytes)

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@router.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # 1. Clean and normalize inputs
    email_clean = user.email.strip().lower()
    username_clean = user.username.strip().lower()

    if not username_clean:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username cannot be empty."
        )

    # 2. Check for duplicate email
    db_email = db.query(models.User).filter(models.User.email == email_clean).first()
    if db_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )
    
    # 3. Check for duplicate username
    db_username = db.query(models.User).filter(models.User.username == username_clean).first()
    if db_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This username is already taken."
        )
    
    # 4. Create User
    hashed_pwd = get_password_hash(user.password)
    new_user = models.User(
        email=email_clean,
        username=username_clean,
        hashed_password=hashed_pwd,
        first_name=user.first_name,
        last_name=user.last_name,
        preferred_currency=user.preferred_currency,
        created_at=datetime.utcnow()
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # 5. Seed Wallet Balances (10,000 USDT/USDC, 10 ETH, 100 SOL)
    starter_balances = [
        models.Balance(user_id=new_user.id, currency="USDT", amount=10000.0),
        models.Balance(user_id=new_user.id, currency="USDC", amount=10000.0),
        models.Balance(user_id=new_user.id, currency="ETH", amount=10.0),
        models.Balance(user_id=new_user.id, currency="SOL", amount=100.0)
    ]
    db.add_all(starter_balances)
    db.commit()
    
    return new_user

@router.post("/login", response_model=schemas.Token)
async def login(credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    login_clean = credentials.username_or_email.strip().lower()

    # 1. Fetch User by email or username
    db_user = db.query(models.User).filter(
        (models.User.email == login_clean) | (models.User.username == login_clean)
    ).first()

    if not db_user or not verify_password(credentials.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 2. Create JWT Access Token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.email},
        expires_delta=access_token_expires
    )
    
    return schemas.Token(
        access_token=access_token,
        token_type="bearer",
        user_email=db_user.email,
        username=db_user.username,
        first_name=db_user.first_name,
        preferred_currency=db_user.preferred_currency
    )
