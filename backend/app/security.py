"""
Business Manager — Security: JWT auth + Argon2 passwords + RBAC helpers.
"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from .models import User, Business, BusinessEmployee

# ── Password hashing ────────────────────────────────────────────────────────
_ph = PasswordHasher(time_cost=2, memory_cost=65536, parallelism=2)

def hash_password(password: str) -> str:
    return _ph.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _ph.verify(hashed, plain)
    except (VerifyMismatchError, VerificationError):
        return False


# ── JWT ─────────────────────────────────────────────────────────────────────
def create_access_token(user_id: int, extra: dict | None = None) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_minutes)
    payload: dict = {"sub": str(user_id), "exp": expires}
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired. Please log in again.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid access token.")


# ── FastAPI dependency ───────────────────────────────────────────────────────
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Session = Depends(get_db),
) -> User:
    payload = decode_token(token)
    user_id = int(payload["sub"])
    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or deactivated.")
    return user


def get_current_active_user(user: User = Depends(get_current_user)) -> User:
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated.")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required.")
    return user


# ── Business ownership helper ────────────────────────────────────────────────
def owned_business(business_id: int, user: User, db: Session) -> Business:
    """Returns Business if current user owns it, else 403."""
    biz = db.get(Business, business_id)
    if not biz:
        raise HTTPException(status_code=404, detail="Business not found.")
    if biz.owner_id != user.id:
        # Check if user is an employee of this business
        emp = db.query(BusinessEmployee).filter_by(
            business_id=business_id, user_id=user.id, is_active=True
        ).first()
        if not emp:
            raise HTTPException(status_code=403, detail="Access denied to this business.")
    return biz


def get_employee_role(business_id: int, user: User, db: Session) -> str:
    """Returns role string for user in given business. 'Owner' if owner."""
    biz = db.get(Business, business_id)
    if biz and biz.owner_id == user.id:
        return "Owner"
    emp = db.query(BusinessEmployee).filter_by(
        business_id=business_id, user_id=user.id, is_active=True
    ).first()
    return emp.role if emp else "None"


# ── RBAC permission map ──────────────────────────────────────────────────────
ROLE_PERMISSIONS: dict[str, set[str]] = {
    "Owner": {"*"},                           # all permissions
    "Manager": {
        "read_dashboard", "manage_orders", "manage_customers",
        "manage_products", "manage_expenses", "manage_payments",
        "manage_suppliers", "manage_projects", "view_reports",
        "manage_employees_view",
    },
    "Salesperson": {
        "read_dashboard", "manage_orders", "manage_customers",
        "read_products", "manage_payments",
    },
    "Accountant": {
        "read_dashboard", "manage_payments", "manage_expenses",
        "view_reports", "read_orders",
    },
    "InventoryManager": {
        "read_dashboard", "manage_products", "manage_suppliers",
        "read_orders",
    },
}

def has_permission(role: str, permission: str) -> bool:
    perms = ROLE_PERMISSIONS.get(role, set())
    return "*" in perms or permission in perms
