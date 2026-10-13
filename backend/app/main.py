"""
Business Manager AI OS — FastAPI Backend
Production-grade API with full CRUD, AI, WhatsApp, economic intelligence.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone, timedelta
from typing import Annotated

from fastapi import FastAPI, Depends, HTTPException, Query, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from sqlalchemy import select, func, desc
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db, engine
from . import models, schemas
from .models import Base
from .security import (
    get_current_user, owned_business, hash_password, verify_password,
    create_access_token, require_admin,
)
from . import ai_service, whatsapp_service, economic_service

# ── App init ─────────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered Business Operating System for Indian MSMEs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)


# ── Helpers ──────────────────────────────────────────────────────────────────
def _now(): return datetime.now(timezone.utc)
def _month_start():
    n = _now(); return n.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
def _day_start():
    n = _now(); return n.replace(hour=0, minute=0, second=0, microsecond=0)

def _get_biz(biz_id: int, user: models.User, db: Session) -> models.Business:
    return owned_business(biz_id, user, db)

def _build_invoice(order: models.Order, db: Session) -> schemas.InvoiceOut:
    biz = db.get(models.Business, order.business_id)
    prod = db.get(models.Product, order.product_id)
    cust = db.get(models.Customer, order.customer_id) if order.customer_id else None
    gst_rate = prod.gst_rate if prod else 18.0
    return schemas.InvoiceOut(
        invoice_no=order.invoice_no or f"INV-{order.id}",
        order_id=order.id,
        business_name=biz.name if biz else "",
        business_address=biz.address if biz else None,
        business_gstin=biz.gstin if biz else None,
        business_phone=biz.phone if biz else None,
        customer_name=cust.name if cust else "Walk-in Customer",
        customer_address=cust.address if cust else None,
        customer_gstin=cust.gstin if cust else None,
        customer_phone=cust.phone if cust else None,
        product_name=prod.name if prod else "Product",
        product_hsn=prod.hsn_code if prod else None,
        quantity=order.quantity,
        unit=prod.unit if prod else "unit",
        unit_price=order.unit_price,
        discount=order.discount,
        taxable_amount=order.taxable_amount,
        gst_rate=gst_rate,
        cgst_amount=order.cgst_amount,
        sgst_amount=order.sgst_amount,
        gst_amount=order.gst_amount,
        delivery_charge=order.delivery_charge,
        total_amount=order.total_amount,
        amount_paid=order.amount_paid,
        balance_due=round(order.total_amount - order.amount_paid, 2),
        status=order.status,
        channel=order.channel,
        invoice_date=order.created_at.strftime("%d %b %Y"),
    )


# ── Root / Health ─────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def root():
    return """<!DOCTYPE html><html><head><title>Business Manager AI OS</title>
    <style>body{font-family:sans-serif;background:#0B1320;color:#F3F4F6;display:flex;
    justify-content:center;align-items:center;height:100vh;margin:0}
    .card{background:#131F33;border:1px solid #1F2E47;border-radius:20px;padding:40px;
    max-width:500px;text-align:center}h1{color:#34D399}a{color:#34D399}</style></head>
    <body><div class="card"><h1>🤖 Business Manager AI OS</h1>
    <p>Backend is running successfully.</p>
    <p><a href="/docs">📖 API Documentation</a> &nbsp;|&nbsp; <a href="/health">❤️ Health Check</a></p>
    </div></body></html>"""

@app.get("/health")
def health():
    return {"status": "ok", "service": "business-manager-ai-os", "version": settings.app_version, "model": settings.gemini_model}


# ═══════════════════════════════════════════════════════════════════
# AUTH
# ═══════════════════════════════════════════════════════════════════

@app.post("/auth/register", response_model=schemas.TokenOut, status_code=201)
def register(body: schemas.RegisterIn, db: Session = Depends(get_db)):
    if db.scalar(select(models.User).where(models.User.email == body.email)):
        raise HTTPException(400, "Email already registered.")
    user = models.User(
        name=body.name.strip(),
        email=body.email.lower().strip(),
        phone=body.phone,
        password_hash=hash_password(body.password),
    )
    db.add(user)
    db.flush()
    # Free subscription
    db.add(models.Subscription(user_id=user.id, plan="free"))
    db.commit()
    token = create_access_token(user.id)
    return schemas.TokenOut(access_token=token, user_id=user.id, user_name=user.name, user_email=user.email, plan="free")


@app.post("/auth/login", response_model=schemas.TokenOut)
def login(body: schemas.LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(models.User).where(models.User.email == body.email.lower().strip()))
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password.")
    if not user.is_active:
        raise HTTPException(403, "Account is deactivated.")
    user.last_login_at = _now()
    db.commit()
    sub = db.scalar(select(models.Subscription).where(models.Subscription.user_id == user.id, models.Subscription.status == "active"))
    plan = sub.plan if sub else "free"
    token = create_access_token(user.id)
    return schemas.TokenOut(access_token=token, user_id=user.id, user_name=user.name, user_email=user.email, plan=plan)


@app.get("/auth/me", response_model=schemas.UserOut)
def me(user: models.User = Depends(get_current_user)):
    return user


@app.put("/auth/me")
def update_profile(body: schemas.RegisterIn, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    user.name = body.name.strip()
    db.commit()
    return {"message": "Profile updated."}


@app.post("/auth/change-password")
def change_password(body: schemas.PasswordChangeIn, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(400, "Current password is incorrect.")
    user.password_hash = hash_password(body.new_password)
    db.commit()
    return {"message": "Password changed successfully."}


# ═══════════════════════════════════════════════════════════════════
# BUSINESSES
# ═══════════════════════════════════════════════════════════════════

@app.get("/businesses", response_model=list[schemas.BusinessOut])
def list_businesses(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return list(db.scalars(select(models.Business).where(
        models.Business.owner_id == user.id, models.Business.is_active == True
    ).order_by(models.Business.created_at)).all())


@app.post("/businesses", response_model=schemas.BusinessOut, status_code=201)
def create_business(body: schemas.BusinessIn, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    biz = models.Business(owner_id=user.id, **body.model_dump())
    db.add(biz)
    db.commit(); db.refresh(biz)
    return biz


@app.get("/businesses/{biz_id}", response_model=schemas.BusinessOut)
def get_business(biz_id: int, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _get_biz(biz_id, user, db)


@app.put("/businesses/{biz_id}", response_model=schemas.BusinessOut)
def update_business(biz_id: int, body: schemas.BusinessIn, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    biz = _get_biz(biz_id, user, db)
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(biz, k, v)
    db.commit(); db.refresh(biz)
    return biz


@app.delete("/businesses/{biz_id}")
def delete_business(biz_id: int, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    biz = _get_biz(biz_id, user, db)
    biz.is_active = False
    db.commit()
    return {"message": "Business deactivated."}


# ── Dashboard ────────────────────────────────────────────────────────────────
@app.get("/businesses/{biz_id}/dashboard", response_model=schemas.DashboardOut)
def dashboard(biz_id: int, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    biz = _get_biz(biz_id, user, db)
    ctx = ai_service.get_business_context(db, biz)

    pending_orders = int(db.scalar(select(func.count()).where(
        models.Order.business_id == biz_id, models.Order.status == "pending")) or 0)
    low_stock = int(db.scalar(select(func.count()).where(
        models.Product.business_id == biz_id, models.Product.is_active == True,
        models.Product.stock_quantity <= models.Product.min_stock_level)) or 0)
    unread = int(db.scalar(select(func.count()).where(
        models.BusinessAlert.business_id == biz_id, models.BusinessAlert.is_read == False)) or 0)
    active_proj = int(db.scalar(select(func.count()).where(
        models.Project.business_id == biz_id, models.Project.status == "In Progress")) or 0)

    return schemas.DashboardOut(
        today_sales=ctx["today_sales"],
        today_expenses=ctx["today_expenses"],
        today_estimated_profit=ctx["today_profit"],
        today_orders_count=ctx["today_orders"],
        month_sales=ctx["month_sales"],
        month_expenses=ctx["month_expenses"],
        month_estimated_profit=ctx["month_profit"],
        month_orders_count=ctx["month_orders"],
        receivables=ctx["total_receivable"],
        pending_orders=pending_orders,
        low_stock_count=low_stock,
        new_customers_this_month=ctx["new_customers_month"],
        active_projects=active_proj,
        health_score=biz.health_score,
        unread_alerts=unread,
    )


# ── Business overview (all businesses combined) ───────────────────────────────
@app.get("/overview")
def combined_overview(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    businesses = list(db.scalars(select(models.Business).where(
        models.Business.owner_id == user.id, models.Business.is_active == True)).all())
    ms = _month_start()
    total = {"total_businesses": len(businesses), "businesses": []}
    overall_sales = overall_profit = overall_receivables = 0.0
    for biz in businesses:
        ctx = ai_service.get_business_context(db, biz)
        overall_sales += ctx["month_sales"]
        overall_profit += ctx["month_profit"]
        overall_receivables += ctx["total_receivable"]
        total["businesses"].append({"id": biz.id, "name": biz.name, "category": biz.category,
                                     "month_sales": ctx["month_sales"], "health_score": biz.health_score})
    total["overall_month_sales"] = round(overall_sales, 2)
    total["overall_month_profit"] = round(overall_profit, 2)
    total["overall_receivables"] = round(overall_receivables, 2)
    return total


# ═══════════════════════════════════════════════════════════════════
# CUSTOMERS
# ═══════════════════════════════════════════════════════════════════

@app.get("/businesses/{biz_id}/customers", response_model=list[schemas.CustomerOut])
def list_customers(biz_id: int, user: models.User = Depends(get_current_user), db: Session = Depends(get_db),
                   q: str | None = Query(None), limit: int = Query(100, le=500)):
    _get_biz(biz_id, user, db)
    stmt = select(models.Customer).where(models.Customer.business_id == biz_id, models.Customer.is_active == True)
    if q:
        stmt = stmt.where(models.Customer.name.ilike(f"%{q}%") | models.Customer.phone.ilike(f"%{q}%"))
    return list(db.scalars(stmt.order_by(desc(models.Customer.last_order_at)).limit(limit)).all())


@app.post("/businesses/{biz_id}/customers", response_model=schemas.CustomerOut, status_code=201)
def create_customer(biz_id: int, body: schemas.CustomerIn, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    _get_biz(biz_id, user, db)
    c = models.Customer(business_id=biz_id, **body.model_dump())
    db.add(c); db.commit(); db.refresh(c)
    return c


@app.get("/businesses/{biz_id}/customers/{cust_id}", response_model=schemas.CustomerOut)
def get_customer(biz_id: int, cust_id: int, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    _get_biz(biz_id, user, db)
    c = db.scalar(select(models.Customer).where(models.Customer.id == cust_id, models.Customer.business_id == biz_id))
    if not c: raise HTTPException(404, "Customer not found.")
    return c


@app.put("/businesses/{biz_id}/customers/{cust_id}", response_model=schemas.CustomerOut)
def update_customer(biz_id: int, cust_id: int, body: schemas.CustomerIn,
                    user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    _get_biz(biz_id, user, db)
    c = db.scalar(select(models.Customer).where(models.Customer.id == cust_id, models.Customer.business_id == biz_id))
    if not c: raise HTTPException(404, "Customer not found.")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(c, k, v)
    db.commit(); db.refresh(c)
    return c


@app.delete("/businesses/{biz_id}/customers/{cust_id}")
def delete_customer(biz_id: int, cust_id: int, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    _get_biz(biz_id, user, db)
    c = db.scalar(select(models.Customer).where(models.Customer.id == cust_id, models.Customer.business_id == biz_id))
    if not c: raise HTTPException(404)
    c.is_active = False
    db.commit()
    return {"message": "Customer deactivated."}


@app.get("/businesses/{biz_id}/customers/{cust_id}/orders", response_model=list[schemas.OrderOut])
def customer_orders(biz_id: int, cust_id: int, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    _get_biz(biz_id, user, db)
    return list(db.scalars(select(models.Order).where(
        models.Order.business_id == biz_id, models.Order.customer_id == cust_id
    ).order_by(desc(models.Order.created_at)).limit(50)).all())


# ═══════════════════════════════════════════════════════════════════
# PRODUCTS / INVENTORY
# ═══════════════════════════════════════════════════════════════════

@app.get("/businesses/{biz_id}/products", response_model=list[schemas.ProductOut])
def list_products(biz_id: int, user: models.User = Depends(get_current_user), db: Session = Depends(get_db),
                  q: str | None = Query(None), category: str | None = Query(None),
                  low_stock_only: bool = Query(False)):
    _get_biz(biz_id, user, db)
    stmt = select(models.Product).where(models.Product.business_id == biz_id, models.Product.is_active == True)
    if q:
        stmt = stmt.where(models.Product.name.ilike(f"%{q}%"))
    if category:
        stmt = stmt.where(models.Product.category == category)
    if low_stock_only:
        stmt = stmt.where(models.Product.stock_quantity <= models.Product.min_stock_level)
    return list(db.scalars(stmt.order_by(models.Product.name)).all())


@app.post("/businesses/{biz_id}/products", response_model=schemas.ProductOut, status_code=201)
def create_product(biz_id: int, body: schemas.ProductIn, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    _get_biz(biz_id, user, db)
    p = models.Product(business_id=biz_id, **body.model_dump())
    db.add(p); db.commit(); db.refresh(p)
    return p


@app.get("/businesses/{biz_id}/products/{prod_id}", response_model=schemas.ProductOut)
def get_product(biz_id: int, prod_id: int, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    _get_biz(biz_id, user, db)
    p = db.scalar(select(models.Product).where(models.Product.id == prod_id, models.Product.business_id == biz_id))
    if not p: raise HTTPException(404, "Product not found.")
    return p


@app.put("/businesses/{biz_id}/products/{prod_id}", response_model=schemas.ProductOut)
def update_product(biz_id: int, prod_id: int, body: schemas.ProductIn,
                   user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    _get_biz(biz_id, user, db)
    p = db.scalar(select(models.Product).where(models.Product.id == prod_id, models.Product.business_id == biz_id))
    if not p: raise HTTPException(404)
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(p, k, v)
    db.commit(); db.refresh(p)
    return p


@app.delete("/businesses/{biz_id}/products/{prod_id}")
def delete_product(biz_id: int, prod_id: int, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    _get_biz(biz_id, user, db)
    p = db.scalar(select(models.Product).where(models.Product.id == prod_id, models.Product.business_id == biz_id))
    if not p: raise HTTPException(404)
    p.is_active = False
    db.commit()
    return {"message": "Product deactivated."}


@app.post("/businesses/{biz_id}/products/{prod_id}/adjust-stock")
def adjust_stock(biz_id: int, prod_id: int, body: schemas.StockAdjustIn,
                 user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    _get_biz(biz_id, user, db)
    p = db.scalar(select(models.Product).where(models.Product.id == prod_id, models.Product.business_id == biz_id))
    if not p: raise HTTPException(404)
    new_qty = round(p.stock_quantity + body.quantity_change, 3)
    if new_qty < 0:
        raise HTTPException(400, "Stock cannot go below zero.")
    p.stock_quantity = new_qty
    db.commit()
    return {"product": p.name, "new_stock": new_qty, "unit": p.unit}


@app.get("/businesses/{biz_id}/inventory/intelligence")
def inventory_intelligence(biz_id: int, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    biz = _get_biz(biz_id, user, db)
    return ai_service.get_inventory_intelligence(db, biz)


# ═══════════════════════════════════════════════════════════════════
# ORDERS
# ═══════════════════════════════════════════════════════════════════

@app.get("/businesses/{biz_id}/orders", response_model=list[schemas.OrderOut])
def list_orders(biz_id: int, user: models.User = Depends(get_current_user), db: Session = Depends(get_db),
                status_filter: str | None = Query(None, alias="status"),
                channel: str | None = Query(None),
                limit: int = Query(100, le=500)):
    _get_biz(biz_id, user, db)
    stmt = select(models.Order).where(models.Order.business_id == biz_id)
    if status_filter:
        stmt = stmt.where(models.Order.status == status_filter)
    if channel:
        stmt = stmt.where(models.Order.channel == channel)
    return list(db.scalars(stmt.order_by(desc(models.Order.created_at)).limit(limit)).all())


@app.post("/businesses/{biz_id}/orders", response_model=schemas.OrderOut, status_code=201)
def create_order(biz_id: int, body: schemas.OrderIn,
                 user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    biz = _get_biz(biz_id, user, db)
    prod = db.scalar(select(models.Product).where(
        models.Product.id == body.product_id, models.Product.business_id == biz_id,
        models.Product.is_active == True).with_for_update())
    if not prod: raise HTTPException(404, "Product not found or inactive.")
    if prod.stock_quantity < body.quantity:
        raise HTTPException(400, f"Insufficient stock. Available: {prod.stock_quantity} {prod.unit}")

    subtotal = round(prod.selling_price * body.quantity, 2)
    if body.discount > subtotal:
        raise HTTPException(400, "Discount cannot exceed subtotal.")
    taxable = round(subtotal - body.discount, 2)
    gst = round(taxable * prod.gst_rate / 100, 2)
    cgst = round(gst / 2, 2)
    sgst = round(gst - cgst, 2)
    total = round(taxable + gst + body.delivery_charge, 2)
    if body.amount_paid > total:
        raise HTTPException(400, "Amount paid cannot exceed total.")

    status_val = "paid" if body.amount_paid >= total else ("partially_paid" if body.amount_paid > 0 else "pending")
    invoice_no = f"INV-{datetime.now().strftime('%Y%m%d')}-{int(datetime.now().timestamp()) % 100000:05d}"

    order = models.Order(
        business_id=biz_id,
        customer_id=body.customer_id,
        product_id=body.product_id,
        quantity=body.quantity,
        unit_price=prod.selling_price,
        mrp=prod.mrp or prod.selling_price,
        discount=body.discount,
        taxable_amount=taxable,
        cgst_amount=cgst,
        sgst_amount=sgst,
        gst_amount=gst,
        total_amount=total,
        cost_amount=round(prod.purchase_price * body.quantity, 2),
        amount_paid=body.amount_paid,
        delivery_charge=body.delivery_charge,
        status=status_val,
        channel=body.channel,
        invoice_no=invoice_no,
        notes=body.notes,
    )
    db.add(order)
    prod.stock_quantity -= body.quantity

    # Update customer stats
    if body.customer_id:
        cust = db.get(models.Customer, body.customer_id)
        if cust:
            cust.total_purchased = round(cust.total_purchased + total, 2)
            cust.total_paid = round(cust.total_paid + body.amount_paid, 2)
            cust.pending_amount = round(cust.pending_amount + (total - body.amount_paid), 2)
            cust.last_order_at = _now()

    # Payment record
    if body.amount_paid > 0:
        db.add(models.Payment(
            business_id=biz_id, order_id=None,
            customer_id=body.customer_id, amount=body.amount_paid, method="upi",
        ))

    db.flush()
    if body.amount_paid > 0:
        db.query(models.Payment).filter(models.Payment.business_id == biz_id,
                                        models.Payment.customer_id == body.customer_id,
                                        models.Payment.order_id == None).order_by(
            desc(models.Payment.created_at)).first().order_id = order.id

    db.commit(); db.refresh(order)
    return order


@app.get("/businesses/{biz_id}/orders/{order_id}", response_model=schemas.OrderOut)
def get_order(biz_id: int, order_id: int, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    _get_biz(biz_id, user, db)
    o = db.scalar(select(models.Order).where(models.Order.id == order_id, models.Order.business_id == biz_id))
    if not o: raise HTTPException(404)
    return o


@app.put("/businesses/{biz_id}/orders/{order_id}/status")
def update_order_status(biz_id: int, order_id: int, body: schemas.OrderStatusUpdateIn,
                        user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    _get_biz(biz_id, user, db)
    o = db.scalar(select(models.Order).where(models.Order.id == order_id, models.Order.business_id == biz_id))
    if not o: raise HTTPException(404)
    if body.status:
        o.status = body.status
    if body.amount_paid is not None:
        extra = body.amount_paid - o.amount_paid
        if extra > 0:
            o.amount_paid = min(body.amount_paid, o.total_amount)
            if o.customer_id:
                cust = db.get(models.Customer, o.customer_id)
                if cust:
                    cust.total_paid = round(cust.total_paid + extra, 2)
                    cust.pending_amount = max(0, round(cust.pending_amount - extra, 2))
        if o.amount_paid >= o.total_amount: o.status = "paid"
    if body.delivery_status:
        o.delivery_status = body.delivery_status
    db.commit()
    return {"message": "Order updated.", "status": o.status, "delivery_status": o.delivery_status}


@app.get("/businesses/{biz_id}/orders/{order_id}/invoice", response_model=schemas.InvoiceOut)
def get_invoice(biz_id: int, order_id: int, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    _get_biz(biz_id, user, db)
    o = db.scalar(select(models.Order).where(models.Order.id == order_id, models.Order.business_id == biz_id))
    if not o: raise HTTPException(404)
    return _build_invoice(o, db)


# ═══════════════════════════════════════════════════════════════════
# EXPENSES
# ═══════════════════════════════════════════════════════════════════

@app.get("/businesses/{biz_id}/expenses", response_model=list[schemas.ExpenseOut])
def list_expenses(biz_id: int, user: models.User = Depends(get_current_user), db: Session = Depends(get_db),
                  category: str | None = Query(None), limit: int = Query(100, le=500)):
    _get_biz(biz_id, user, db)
    stmt = select(models.Expense).where(models.Expense.business_id == biz_id)
    if category:
        stmt = stmt.where(models.Expense.category == category)
    return list(db.scalars(stmt.order_by(desc(models.Expense.created_at)).limit(limit)).all())


@app.post("/businesses/{biz_id}/expenses", response_model=schemas.ExpenseOut, status_code=201)
def create_expense(biz_id: int, body: schemas.ExpenseIn, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    _get_biz(biz_id, user, db)
    e = models.Expense(business_id=biz_id, **body.model_dump())
    db.add(e); db.commit(); db.refresh(e)
    return e


@app.delete("/businesses/{biz_id}/expenses/{exp_id}")
def delete_expense(biz_id: int, exp_id: int, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    _get_biz(biz_id, user, db)
    e = db.scalar(select(models.Expense).where(models.Expense.id == exp_id, models.Expense.business_id == biz_id))
    if not e: raise HTTPException(404)
    db.delete(e); db.commit()
    return {"message": "Expense deleted."}


# ═══════════════════════════════════════════════════════════════════
# PAYMENTS
# ═══════════════════════════════════════════════════════════════════

@app.get("/businesses/{biz_id}/payments", response_model=list[schemas.PaymentOut])
def list_payments(biz_id: int, user: models.User = Depends(get_current_user), db: Session = Depends(get_db), limit: int = Query(100, le=500)):
    _get_biz(biz_id, user, db)
    return list(db.scalars(select(models.Payment).where(models.Payment.business_id == biz_id)
                           .order_by(desc(models.Payment.created_at)).limit(limit)).all())


@app.post("/businesses/{biz_id}/payments", response_model=schemas.PaymentOut, status_code=201)
def record_payment(biz_id: int, body: schemas.PaymentIn, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    _get_biz(biz_id, user, db)
    pay = models.Payment(business_id=biz_id, **body.model_dump())
    db.add(pay)
    # Update order if provided
    if body.order_id:
        o = db.scalar(select(models.Order).where(models.Order.id == body.order_id, models.Order.business_id == biz_id))
        if o:
            o.amount_paid = min(round(o.amount_paid + body.amount, 2), o.total_amount)
            o.status = "paid" if o.amount_paid >= o.total_amount else "partially_paid"
            if body.customer_id:
                c = db.get(models.Customer, body.customer_id)
                if c:
                    c.total_paid = round(c.total_paid + body.amount, 2)
                    c.pending_amount = max(0, round(c.pending_amount - body.amount, 2))
    db.commit(); db.refresh(pay)
    return pay


# ═══════════════════════════════════════════════════════════════════
# SUPPLIERS
# ═══════════════════════════════════════════════════════════════════

@app.get("/businesses/{biz_id}/suppliers", response_model=list[schemas.SupplierOut])
def list_suppliers(biz_id: int, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    _get_biz(biz_id, user, db)
    return list(db.scalars(select(models.Supplier).where(
        models.Supplier.business_id == biz_id, models.Supplier.is_active == True
    ).order_by(models.Supplier.name)).all())


@app.post("/businesses/{biz_id}/suppliers", response_model=schemas.SupplierOut, status_code=201)
def create_supplier(biz_id: int, body: schemas.SupplierIn, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    _get_biz(biz_id, user, db)
    s = models.Supplier(business_id=biz_id, **body.model_dump())
    db.add(s); db.commit(); db.refresh(s)
    return s


@app.put("/businesses/{biz_id}/suppliers/{sup_id}", response_model=schemas.SupplierOut)
def update_supplier(biz_id: int, sup_id: int, body: schemas.SupplierIn,
                    user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    _get_biz(biz_id, user, db)
    s = db.scalar(select(models.Supplier).where(models.Supplier.id == sup_id, models.Supplier.business_id == biz_id))
    if not s: raise HTTPException(404)
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(s, k, v)
    db.commit(); db.refresh(s)
    return s


@app.delete("/businesses/{biz_id}/suppliers/{sup_id}")
def delete_supplier(biz_id: int, sup_id: int, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    _get_biz(biz_id, user, db)
    s = db.scalar(select(models.Supplier).where(models.Supplier.id == sup_id, models.Supplier.business_id == biz_id))
    if not s: raise HTTPException(404)
    s.is_active = False; db.commit()
    return {"message": "Supplier removed."}


# ═══════════════════════════════════════════════════════════════════
# PROJECTS
# ═══════════════════════════════════════════════════════════════════

@app.get("/businesses/{biz_id}/projects", response_model=list[schemas.ProjectOut])
def list_projects(biz_id: int, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    _get_biz(biz_id, user, db)
    return list(db.scalars(select(models.Project).where(models.Project.business_id == biz_id)
                           .order_by(desc(models.Project.created_at))).all())


@app.post("/businesses/{biz_id}/projects", response_model=schemas.ProjectOut, status_code=201)
def create_project(biz_id: int, body: schemas.ProjectIn, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    _get_biz(biz_id, user, db)
    p = models.Project(business_id=biz_id, **body.model_dump())
    db.add(p); db.commit(); db.refresh(p)
    return p


@app.put("/businesses/{biz_id}/projects/{proj_id}", response_model=schemas.ProjectOut)
def update_project(biz_id: int, proj_id: int, body: schemas.ProjectIn,
                   user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    _get_biz(biz_id, user, db)
    p = db.scalar(select(models.Project).where(models.Project.id == proj_id, models.Project.business_id == biz_id))
    if not p: raise HTTPException(404)
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(p, k, v)
    db.commit(); db.refresh(p)
    return p


@app.delete("/businesses/{biz_id}/projects/{proj_id}")
def delete_project(biz_id: int, proj_id: int, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    _get_biz(biz_id, user, db)
    p = db.scalar(select(models.Project).where(models.Project.id == proj_id, models.Project.business_id == biz_id))
    if not p: raise HTTPException(404)
    db.delete(p); db.commit()
    return {"message": "Project deleted."}


# ═══════════════════════════════════════════════════════════════════
# QUOTATIONS
# ═══════════════════════════════════════════════════════════════════

@app.get("/businesses/{biz_id}/quotations", response_model=list[schemas.QuotationOut])
def list_quotations(biz_id: int, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    _get_biz(biz_id, user, db)
    return list(db.scalars(select(models.Quotation).where(models.Quotation.business_id == biz_id)
                           .order_by(desc(models.Quotation.created_at)).limit(100)).all())


@app.post("/businesses/{biz_id}/quotations", response_model=schemas.QuotationOut, status_code=201)
def create_quotation(biz_id: int, body: schemas.QuotationIn,
                     user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    _get_biz(biz_id, user, db)
    prod = db.scalar(select(models.Product).where(models.Product.id == body.product_id, models.Product.business_id == biz_id))
    if not prod: raise HTTPException(404, "Product not found.")
    subtotal = round(prod.selling_price * body.quantity, 2)
    taxable = round(subtotal - body.discount, 2)
    gst = round(taxable * prod.gst_rate / 100, 2)
    total = round(taxable + gst + body.delivery_charge, 2)
    qno = f"QT-{datetime.now().strftime('%Y%m%d')}-{int(datetime.now().timestamp()) % 10000:04d}"
    q = models.Quotation(
        business_id=biz_id, customer_id=body.customer_id, product_id=body.product_id,
        quotation_no=qno, quantity=body.quantity, unit_price=prod.selling_price,
        discount=body.discount, gst_amount=gst, total_amount=total,
        validity_days=body.validity_days, notes=body.notes,
    )
    db.add(q); db.commit(); db.refresh(q)
    return q


@app.post("/businesses/{biz_id}/quotations/{quot_id}/convert")
def convert_quotation(biz_id: int, quot_id: int, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    _get_biz(biz_id, user, db)
    q = db.scalar(select(models.Quotation).where(models.Quotation.id == quot_id, models.Quotation.business_id == biz_id))
    if not q: raise HTTPException(404)
    if q.status in ("converted", "rejected"): raise HTTPException(400, f"Quotation already {q.status}.")
    prod = db.scalar(select(models.Product).where(models.Product.id == q.product_id).with_for_update())
    if not prod or prod.stock_quantity < q.quantity:
        raise HTTPException(400, "Insufficient stock.")
    prod.stock_quantity -= q.quantity
    invoice_no = f"INV-{datetime.now().strftime('%Y%m%d')}-{int(datetime.now().timestamp()) % 100000:05d}"
    order = models.Order(
        business_id=biz_id, customer_id=q.customer_id, product_id=q.product_id,
        quantity=q.quantity, unit_price=q.unit_price, discount=q.discount,
        taxable_amount=round(q.unit_price * q.quantity - q.discount, 2),
        gst_amount=q.gst_amount, cgst_amount=round(q.gst_amount / 2, 2),
        sgst_amount=round(q.gst_amount - round(q.gst_amount / 2, 2), 2),
        total_amount=q.total_amount, cost_amount=round(prod.purchase_price * q.quantity, 2),
        amount_paid=0, status="pending", channel="app", invoice_no=invoice_no,
    )
    db.add(order); db.flush()
    q.status = "converted"; q.order_id = order.id
    db.commit()
    return {"message": "Quotation converted to order.", "order_id": order.id, "invoice_no": invoice_no}


# ═══════════════════════════════════════════════════════════════════
# ALERTS
# ═══════════════════════════════════════════════════════════════════

@app.get("/businesses/{biz_id}/alerts", response_model=list[schemas.AlertOut])
def list_alerts(biz_id: int, user: models.User = Depends(get_current_user), db: Session = Depends(get_db),
                unread_only: bool = Query(False)):
    _get_biz(biz_id, user, db)
    stmt = select(models.BusinessAlert).where(models.BusinessAlert.business_id == biz_id)
    if unread_only:
        stmt = stmt.where(models.BusinessAlert.is_read == False)
    return list(db.scalars(stmt.order_by(desc(models.BusinessAlert.created_at)).limit(50)).all())


@app.post("/businesses/{biz_id}/alerts/{alert_id}/read")
def mark_alert_read(biz_id: int, alert_id: int, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    _get_biz(biz_id, user, db)
    a = db.scalar(select(models.BusinessAlert).where(models.BusinessAlert.id == alert_id, models.BusinessAlert.business_id == biz_id))
    if a: a.is_read = True; db.commit()
    return {"message": "Alert marked as read."}


@app.post("/businesses/{biz_id}/alerts/read-all")
def mark_all_alerts_read(biz_id: int, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    _get_biz(biz_id, user, db)
    db.query(models.BusinessAlert).filter_by(business_id=biz_id, is_read=False).update({"is_read": True})
    db.commit()
    return {"message": "All alerts marked as read."}


# ═══════════════════════════════════════════════════════════════════
# EMPLOYEES
# ═══════════════════════════════════════════════════════════════════

@app.get("/businesses/{biz_id}/employees")
def list_employees(biz_id: int, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    _get_biz(biz_id, user, db)
    rows = list(db.scalars(select(models.BusinessEmployee).where(
        models.BusinessEmployee.business_id == biz_id, models.BusinessEmployee.is_active == True
    )).all())
    return [{"id": r.id, "role": r.role, "joined_at": r.joined_at, "user_id": r.user_id} for r in rows]


@app.post("/businesses/{biz_id}/employees", status_code=201)
def add_employee(biz_id: int, body: schemas.EmployeeIn, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    _get_biz(biz_id, user, db)
    # Find or create user by phone
    emp_user = db.scalar(select(models.User).where(models.User.phone == body.phone))
    if not emp_user:
        emp_user = models.User(name=body.name, email=f"{body.phone}@staff.bm", phone=body.phone,
                               password_hash=hash_password("ChangeMe@123"))
        db.add(emp_user); db.flush()
    emp = models.BusinessEmployee(business_id=biz_id, user_id=emp_user.id, role=body.role, joined_at=_now())
    db.add(emp); db.commit()
    return {"message": "Employee added.", "user_id": emp_user.id}


# ═══════════════════════════════════════════════════════════════════
# AI ENDPOINTS
# ═══════════════════════════════════════════════════════════════════

@app.get("/businesses/{biz_id}/ai/query")
def ai_query(biz_id: int, q: str = Query(..., min_length=2),
             user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    biz = _get_biz(biz_id, user, db)
    return ai_service.answer_business_query(db, biz, q)


@app.get("/businesses/{biz_id}/ai/action-plan")
def ai_action_plan(biz_id: int, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    biz = _get_biz(biz_id, user, db)
    return ai_service.get_action_plan(db, biz)


@app.get("/businesses/{biz_id}/ai/health-score")
def ai_health_score(biz_id: int, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    biz = _get_biz(biz_id, user, db)
    result = ai_service.compute_health_score(db, biz)
    biz.health_score = result["score"]
    biz.health_score_updated_at = _now()
    db.commit()
    return result


@app.get("/businesses/{biz_id}/ai/recommendations")
def ai_recommendations(biz_id: int, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    biz = _get_biz(biz_id, user, db)
    return ai_service.get_ai_recommendations(db, biz)


# ═══════════════════════════════════════════════════════════════════
# WHATSAPP
# ═══════════════════════════════════════════════════════════════════

@app.post("/businesses/{biz_id}/whatsapp/simulate")
def whatsapp_simulate(biz_id: int, body: schemas.WhatsAppSimIn,
                      user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    biz = _get_biz(biz_id, user, db)
    return whatsapp_service.process_message(db, biz, body.customer_phone, body.customer_name, body.message_text)


@app.get("/businesses/{biz_id}/whatsapp/chats", response_model=list[schemas.WhatsAppChatOut])
def whatsapp_chats(biz_id: int, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    _get_biz(biz_id, user, db)
    return list(db.scalars(select(models.WhatsAppChat).where(models.WhatsAppChat.business_id == biz_id)
                           .order_by(desc(models.WhatsAppChat.created_at)).limit(100)).all())


@app.post("/businesses/{biz_id}/whatsapp/reminder")
def whatsapp_reminder(biz_id: int, body: schemas.PaymentReminderIn,
                      user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    biz = _get_biz(biz_id, user, db)
    msg = whatsapp_service.generate_payment_reminder(
        body.customer_name, body.pending_amount,
        body.business_name or biz.name, body.days_overdue
    )
    return {"message": msg, "customer": body.customer_name, "amount": body.pending_amount}


# ═══════════════════════════════════════════════════════════════════
# ECONOMIC INTELLIGENCE
# ═══════════════════════════════════════════════════════════════════

@app.get("/businesses/{biz_id}/intelligence")
def economic_intelligence(biz_id: int, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    biz = _get_biz(biz_id, user, db)
    return economic_service.get_economic_intelligence(biz.category)


@app.get("/businesses/{biz_id}/intelligence/market-impact")
def market_impact(biz_id: int, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    biz = _get_biz(biz_id, user, db)
    analysis = economic_service.get_market_impact_analysis(biz.category, biz.name)
    return {"analysis": analysis, "business": biz.name, "category": biz.category,
            "disclaimer": "AI interpretation only. Verify from official sources."}


@app.get("/intelligence/tenders/{tender_id}/summary")
def tender_summary(tender_id: str, category: str = Query("Construction"),
                   user: models.User = Depends(get_current_user)):
    return {"summary": economic_service.get_tender_ai_summary(tender_id, category)}


# ═══════════════════════════════════════════════════════════════════
# REPORTS
# ═══════════════════════════════════════════════════════════════════

@app.get("/businesses/{biz_id}/reports/summary", response_model=schemas.BusinessReportOut)
def report_summary(biz_id: int, period: str = Query("month", enum=["today", "week", "month", "year"]),
                   user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    biz = _get_biz(biz_id, user, db)
    now = _now()
    if period == "today":
        start = _day_start()
    elif period == "week":
        start = now - timedelta(days=7)
    elif period == "month":
        start = _month_start()
    else:
        start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

    orders = list(db.scalars(select(models.Order).where(
        models.Order.business_id == biz_id, models.Order.created_at >= start,
        models.Order.status != "cancelled"
    )).all())
    expenses = list(db.scalars(select(models.Expense).where(
        models.Expense.business_id == biz_id, models.Expense.created_at >= start
    )).all())

    revenue = round(sum(o.total_amount for o in orders), 2)
    cogs = round(sum(o.cost_amount for o in orders), 2)
    total_exp = round(sum(e.amount for e in expenses), 2)
    gross = round(revenue - cogs, 2)
    net = round(gross - total_exp, 2)
    avg_order = round(revenue / len(orders), 2) if orders else 0.0
    receivables = round(sum(o.total_amount - o.amount_paid for o in orders), 2)

    # Top products
    prod_map: dict[int, dict] = {}
    for o in orders:
        if o.product_id not in prod_map:
            prod = db.get(models.Product, o.product_id)
            prod_map[o.product_id] = {"name": prod.name if prod else f"#{o.product_id}", "qty": 0, "revenue": 0}
        prod_map[o.product_id]["qty"] += o.quantity
        prod_map[o.product_id]["revenue"] += o.total_amount
    top_prods = sorted(prod_map.values(), key=lambda x: x["revenue"], reverse=True)[:5]

    # Expense breakdown
    exp_map: dict[str, float] = {}
    for e in expenses:
        exp_map[e.category] = round(exp_map.get(e.category, 0) + e.amount, 2)
    exp_breakdown = [{"category": k, "amount": v} for k, v in sorted(exp_map.items(), key=lambda x: x[1], reverse=True)]

    # Top customers
    cust_map: dict[int, dict] = {}
    for o in orders:
        if o.customer_id:
            if o.customer_id not in cust_map:
                c = db.get(models.Customer, o.customer_id)
                cust_map[o.customer_id] = {"name": c.name if c else f"#{o.customer_id}", "revenue": 0}
            cust_map[o.customer_id]["revenue"] += o.total_amount
    top_customers = sorted(cust_map.values(), key=lambda x: x["revenue"], reverse=True)[:5]

    return schemas.BusinessReportOut(
        period=period,
        total_revenue=revenue,
        total_cost_of_goods=cogs,
        total_expenses=total_exp,
        gross_profit=gross,
        estimated_net_profit=net,
        profit_margin_pct=round(net / revenue * 100, 1) if revenue else 0.0,
        total_orders_count=len(orders),
        average_order_value=avg_order,
        total_receivables=receivables,
        total_payables=0.0,
        top_selling_products=top_prods,
        expense_breakdown=exp_breakdown,
        top_customers=top_customers,
        monthly_trend=[],
    )


# ═══════════════════════════════════════════════════════════════════
# GLOBAL SEARCH
# ═══════════════════════════════════════════════════════════════════

@app.get("/businesses/{biz_id}/search", response_model=list[schemas.SearchResultItem])
def global_search(biz_id: int, q: str = Query(..., min_length=2),
                  user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    _get_biz(biz_id, user, db)
    results: list[schemas.SearchResultItem] = []
    term = f"%{q}%"

    for c in db.scalars(select(models.Customer).where(
            models.Customer.business_id == biz_id, models.Customer.name.ilike(term)).limit(5)):
        results.append(schemas.SearchResultItem(type="customer", id=c.id, title=c.name,
                        subtitle=c.phone or "No phone", extra=f"₹{c.pending_amount:,.0f} pending"))

    for p in db.scalars(select(models.Product).where(
            models.Product.business_id == biz_id, models.Product.name.ilike(term),
            models.Product.is_active == True).limit(5)):
        results.append(schemas.SearchResultItem(type="product", id=p.id, title=p.name,
                        subtitle=f"₹{p.selling_price:,.2f}/{p.unit}", extra=f"Stock: {p.stock_quantity} {p.unit}"))

    for o in db.scalars(select(models.Order).where(
            models.Order.business_id == biz_id, models.Order.invoice_no.ilike(term)).limit(5)):
        results.append(schemas.SearchResultItem(type="order", id=o.id, title=o.invoice_no or f"Order #{o.id}",
                        subtitle=f"₹{o.total_amount:,.2f}", extra=o.status))

    for s in db.scalars(select(models.Supplier).where(
            models.Supplier.business_id == biz_id, models.Supplier.name.ilike(term),
            models.Supplier.is_active == True).limit(3)):
        results.append(schemas.SearchResultItem(type="supplier", id=s.id, title=s.name,
                        subtitle=s.category or "", extra=f"₹{s.pending_payable:,.0f} payable"))

    return results


# ═══════════════════════════════════════════════════════════════════
# SUBSCRIPTION
# ═══════════════════════════════════════════════════════════════════

@app.get("/subscription", response_model=schemas.SubscriptionOut)
def get_subscription(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    sub = db.scalar(select(models.Subscription).where(
        models.Subscription.user_id == user.id, models.Subscription.status == "active"
    ))
    if not sub:
        sub = models.Subscription(user_id=user.id, plan="free")
        db.add(sub); db.commit(); db.refresh(sub)
    return sub


# ═══════════════════════════════════════════════════════════════════
# ADMIN (protected)
# ═══════════════════════════════════════════════════════════════════

@app.get("/admin/stats")
def admin_stats(admin: models.User = Depends(require_admin), db: Session = Depends(get_db)):
    return {
        "total_users": db.scalar(select(func.count()).select_from(models.User)),
        "total_businesses": db.scalar(select(func.count()).select_from(models.Business).where(models.Business.is_active == True)),
        "total_orders": db.scalar(select(func.count()).select_from(models.Order)),
        "total_revenue": db.scalar(select(func.coalesce(func.sum(models.Order.total_amount), 0)).where(models.Order.status != "cancelled")),
    }
