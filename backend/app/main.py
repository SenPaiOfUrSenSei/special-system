from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from sqlalchemy import text
from alembic.config import Config
from alembic import command
from app.database import engine, Base
from app import models
from app.routers import auth, bridge

# Programmatically run Alembic migrations on startup to ensure DB is upgraded
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(current_dir)
    alembic_ini_path = os.path.join(backend_dir, "alembic.ini")
    
    alembic_cfg = Config(alembic_ini_path)
    alembic_cfg.set_main_option("script_location", os.path.join(backend_dir, "alembic"))
    
    # Run upgrade head
    command.upgrade(alembic_cfg, "head")
    print("Programmatic Alembic migration upgrade to 'head' succeeded.")
except Exception as e:
    print(f"Alembic startup upgrade failed: {e}")
    # Rollback database transaction state to clear aborted connections
    try:
        with engine.connect() as conn:
            conn.execute(text("ROLLBACK;"))
            conn.commit()
    except Exception as rb_err:
        print(f"Rollback failed: {rb_err}")

# Create any missing tables (like balances)
try:
    Base.metadata.create_all(bind=engine)
    
    # Seed initial system pools if they don't exist
    from app.database import SessionLocal
    from sqlalchemy.sql import func
    db = SessionLocal()
    try:
        if db.query(models.SystemPool).count() == 0:
            print("Seeding initial system pools...")
            currencies = ["USDT", "USDC", "ETH", "SOL"]
            for curr in currencies:
                balance_sum = db.query(func.sum(models.Balance.amount)).filter(models.Balance.currency == curr).scalar() or 0.0
                new_pool = models.SystemPool(
                    currency=curr,
                    tracked_balance=balance_sum,
                    exposure=0.0
                )
                db.add(new_pool)
            db.commit()
            print("Seeding system pools complete.")
    except Exception as seed_err:
        print(f"Failed to seed system pools: {seed_err}")
    finally:
        db.close()
except Exception as e:
    print(f"Base.metadata.create_all failed: {e}")


app = FastAPI(
    title="Bridgr L2 API",
    description="Backend service for Bridgr Layer 2 cross-chain atomic swaps with PostgreSQL database support.",
    version="2.0.0"
)

# Set up CORS middleware to allow cross-origin requests from Vite React app
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", "http://127.0.0.1:5173",
        "http://localhost:5174", "http://127.0.0.1:5174",
        "http://localhost:5175", "http://127.0.0.1:5175"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router, prefix="/api")
app.include_router(bridge.router, prefix="/api")

import asyncio
from app import settlement_worker

@app.on_event("startup")
async def startup_event():
    # Start the settlement decision scheduler in the background
    asyncio.create_task(settlement_worker.start_scheduler())

@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "Bridgr L2 DB Engine",
        "version": "2.0.0"
    }
