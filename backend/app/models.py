"""
Business Manager — SQLAlchemy ORM Models
Production-grade schema with full Phase 1 entities.
"""
from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy import (
    String, Integer, Float, DateTime, ForeignKey,
    Boolean, Text, Enum, UniqueConstraint, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# USER & AUTHENTICATION
# ---------------------------------------------------------------------------

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    preferred_language: Mapped[str] = mapped_column(String(10), default="en")  # en, hi, or
    profile_photo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)

    businesses: Mapped[list["Business"]] = relationship(back_populates="owner", cascade="all, delete-orphan")
    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="user", cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# BUSINESS
# ---------------------------------------------------------------------------

class Business(Base):
    __tablename__ = "businesses"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(160))
    category: Mapped[str] = mapped_column(String(60), default="Retail")
    # Retail | Construction | Agriculture | Wholesale | Manufacturing |
    # Restaurant | Pharmacy | Transport | School | Other
    sub_category: Mapped[str | None] = mapped_column(String(80), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    gstin: Mapped[str | None] = mapped_column(String(20), nullable=True)
    pan: Mapped[str | None] = mapped_column(String(15), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str | None] = mapped_column(String(80), nullable=True)
    state: Mapped[str | None] = mapped_column(String(80), nullable=True, default="Odisha")
    pincode: Mapped[str | None] = mapped_column(String(10), nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    health_score: Mapped[int] = mapped_column(Integer, default=85)
    health_score_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    whatsapp_connected: Mapped[bool] = mapped_column(Boolean, default=False)
    whatsapp_phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)

    owner: Mapped["User"] = relationship(back_populates="businesses")
    employees: Mapped[list["BusinessEmployee"]] = relationship(back_populates="business", cascade="all, delete-orphan")
    customers: Mapped[list["Customer"]] = relationship(back_populates="business", cascade="all, delete-orphan")
    products: Mapped[list["Product"]] = relationship(back_populates="business", cascade="all, delete-orphan")
    orders: Mapped[list["Order"]] = relationship(back_populates="business", cascade="all, delete-orphan")
    expenses: Mapped[list["Expense"]] = relationship(back_populates="business", cascade="all, delete-orphan")
    payments: Mapped[list["Payment"]] = relationship(back_populates="business", cascade="all, delete-orphan")
    projects: Mapped[list["Project"]] = relationship(back_populates="business", cascade="all, delete-orphan")
    suppliers: Mapped[list["Supplier"]] = relationship(back_populates="business", cascade="all, delete-orphan")
    quotations: Mapped[list["Quotation"]] = relationship(back_populates="business", cascade="all, delete-orphan")
    alerts: Mapped[list["BusinessAlert"]] = relationship(back_populates="business", cascade="all, delete-orphan")
    whatsapp_chats: Mapped[list["WhatsAppChat"]] = relationship(back_populates="business", cascade="all, delete-orphan")
    tenders: Mapped[list["Tender"]] = relationship(back_populates="business", cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# EMPLOYEE / RBAC
# ---------------------------------------------------------------------------

class BusinessEmployee(Base):
    """Employees linked to a business with role-based permissions."""
    __tablename__ = "business_employees"
    __table_args__ = (
        UniqueConstraint("business_id", "user_id", name="uq_biz_user"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    # Owner | Manager | Salesperson | Accountant | InventoryManager
    role: Mapped[str] = mapped_column(String(50), default="Salesperson")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    invited_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    joined_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    business: Mapped["Business"] = relationship(back_populates="employees")
    user: Mapped["User"] = relationship()


# ---------------------------------------------------------------------------
# CUSTOMER
# ---------------------------------------------------------------------------

class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(160), index=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True, index=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str | None] = mapped_column(String(80), nullable=True)
    gstin: Mapped[str | None] = mapped_column(String(20), nullable=True)
    pan: Mapped[str | None] = mapped_column(String(15), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    credit_limit: Mapped[float] = mapped_column(Float, default=0.0)
    total_purchased: Mapped[float] = mapped_column(Float, default=0.0)
    total_paid: Mapped[float] = mapped_column(Float, default=0.0)
    pending_amount: Mapped[float] = mapped_column(Float, default=0.0)
    last_order_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)

    business: Mapped["Business"] = relationship(back_populates="customers")
    orders: Mapped[list["Order"]] = relationship(back_populates="customer")
    payments: Mapped[list["Payment"]] = relationship(back_populates="customer")


# ---------------------------------------------------------------------------
# PRODUCT / INVENTORY
# ---------------------------------------------------------------------------

class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(160), index=True)
    sku: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    barcode: Mapped[str | None] = mapped_column(String(80), nullable=True)
    category: Mapped[str | None] = mapped_column(String(80), default="General", index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    unit: Mapped[str] = mapped_column(String(30), default="unit")
    purchase_price: Mapped[float] = mapped_column(Float, default=0.0)
    selling_price: Mapped[float] = mapped_column(Float, default=0.0)
    mrp: Mapped[float] = mapped_column(Float, default=0.0)
    stock_quantity: Mapped[float] = mapped_column(Float, default=0.0)
    reserved_quantity: Mapped[float] = mapped_column(Float, default=0.0)
    min_stock_level: Mapped[float] = mapped_column(Float, default=5.0)
    max_stock_level: Mapped[float] = mapped_column(Float, default=1000.0)
    gst_rate: Mapped[float] = mapped_column(Float, default=18.0)
    hsn_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    supplier_id: Mapped[int | None] = mapped_column(ForeignKey("suppliers.id", ondelete="SET NULL"), nullable=True)
    warehouse_location: Mapped[str | None] = mapped_column(String(80), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)

    business: Mapped["Business"] = relationship(back_populates="products")
    supplier: Mapped["Supplier | None"] = relationship(foreign_keys=[supplier_id])


# ---------------------------------------------------------------------------
# ORDER
# ---------------------------------------------------------------------------

class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        Index("ix_orders_business_created", "business_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), index=True)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id", ondelete="SET NULL"), nullable=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    quantity: Mapped[float] = mapped_column(Float)
    unit_price: Mapped[float] = mapped_column(Float)
    mrp: Mapped[float] = mapped_column(Float, default=0.0)
    discount: Mapped[float] = mapped_column(Float, default=0.0)
    taxable_amount: Mapped[float] = mapped_column(Float, default=0.0)
    cgst_amount: Mapped[float] = mapped_column(Float, default=0.0)
    sgst_amount: Mapped[float] = mapped_column(Float, default=0.0)
    igst_amount: Mapped[float] = mapped_column(Float, default=0.0)
    gst_amount: Mapped[float] = mapped_column(Float, default=0.0)
    total_amount: Mapped[float] = mapped_column(Float)
    cost_amount: Mapped[float] = mapped_column(Float, default=0.0)
    amount_paid: Mapped[float] = mapped_column(Float, default=0.0)
    delivery_charge: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(30), default="pending", index=True)
    # pending | partially_paid | paid | cancelled | refunded
    channel: Mapped[str] = mapped_column(String(30), default="app")
    # app | whatsapp | voice | walk_in | phone
    delivery_status: Mapped[str] = mapped_column(String(30), default="pending")
    # pending | dispatched | delivered | returned
    invoice_no: Mapped[str | None] = mapped_column(String(60), nullable=True, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)

    business: Mapped["Business"] = relationship(back_populates="orders")
    customer: Mapped["Customer | None"] = relationship(back_populates="orders")
    product: Mapped["Product"] = relationship()
    payments: Mapped[list["Payment"]] = relationship(back_populates="order")


# ---------------------------------------------------------------------------
# EXPENSE
# ---------------------------------------------------------------------------

class Expense(Base):
    __tablename__ = "expenses"
    __table_args__ = (
        Index("ix_expenses_business_created", "business_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), index=True)
    category: Mapped[str] = mapped_column(String(80), index=True)
    # Transport | Labour | Electricity | Raw Material | Rent | Fuel |
    # Maintenance | Marketing | Salary | Other
    description: Mapped[str] = mapped_column(String(255))
    amount: Mapped[float] = mapped_column(Float)
    payment_method: Mapped[str] = mapped_column(String(30), default="cash")
    receipt_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    supplier_id: Mapped[int | None] = mapped_column(ForeignKey("suppliers.id", ondelete="SET NULL"), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, index=True)

    business: Mapped["Business"] = relationship(back_populates="expenses")


# ---------------------------------------------------------------------------
# PAYMENT
# ---------------------------------------------------------------------------

class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (
        Index("ix_payments_business_created", "business_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), index=True)
    order_id: Mapped[int | None] = mapped_column(ForeignKey("orders.id", ondelete="SET NULL"), nullable=True)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id", ondelete="SET NULL"), nullable=True)
    amount: Mapped[float] = mapped_column(Float)
    method: Mapped[str] = mapped_column(String(30), default="upi")
    # upi | cash | bank_transfer | cheque | card | neft | rtgs
    reference: Mapped[str | None] = mapped_column(String(120), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, index=True)

    business: Mapped["Business"] = relationship(back_populates="payments")
    order: Mapped["Order | None"] = relationship(back_populates="payments")
    customer: Mapped["Customer | None"] = relationship(back_populates="payments")


# ---------------------------------------------------------------------------
# SUPPLIER
# ---------------------------------------------------------------------------

class Supplier(Base):
    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(primary_key=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(160), index=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    category: Mapped[str | None] = mapped_column(String(80), default="Raw Materials")
    gstin: Mapped[str | None] = mapped_column(String(20), nullable=True)
    pan: Mapped[str | None] = mapped_column(String(15), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str | None] = mapped_column(String(80), nullable=True)
    total_purchased: Mapped[float] = mapped_column(Float, default=0.0)
    pending_payable: Mapped[float] = mapped_column(Float, default=0.0)
    rating: Mapped[float] = mapped_column(Float, default=4.5)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

    business: Mapped["Business"] = relationship(back_populates="suppliers")


# ---------------------------------------------------------------------------
# PROJECT (Construction / Contractors)
# ---------------------------------------------------------------------------

class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    client_name: Mapped[str] = mapped_column(String(160))
    client_phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    location: Mapped[str | None] = mapped_column(String(160), nullable=True)
    contract_value: Mapped[float] = mapped_column(Float, default=0.0)
    spent_amount: Mapped[float] = mapped_column(Float, default=0.0)
    advance_received: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(40), default="In Progress")
    # Planning | In Progress | On Hold | Completed | Cancelled
    start_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    deadline: Mapped[str | None] = mapped_column(String(20), nullable=True)
    completion_percentage: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)

    business: Mapped["Business"] = relationship(back_populates="projects")


# ---------------------------------------------------------------------------
# QUOTATION
# ---------------------------------------------------------------------------

class Quotation(Base):
    __tablename__ = "quotations"

    id: Mapped[int] = mapped_column(primary_key=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), index=True)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id", ondelete="SET NULL"), nullable=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    quotation_no: Mapped[str] = mapped_column(String(60), index=True)
    quantity: Mapped[float] = mapped_column(Float)
    unit_price: Mapped[float] = mapped_column(Float)
    discount: Mapped[float] = mapped_column(Float, default=0.0)
    gst_amount: Mapped[float] = mapped_column(Float, default=0.0)
    total_amount: Mapped[float] = mapped_column(Float)
    validity_days: Mapped[int] = mapped_column(Integer, default=15)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="pending")
    # pending | sent | accepted | rejected | converted | expired
    order_id: Mapped[int | None] = mapped_column(ForeignKey("orders.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

    business: Mapped["Business"] = relationship(back_populates="quotations")
    customer: Mapped["Customer | None"] = relationship()
    product: Mapped["Product"] = relationship()


# ---------------------------------------------------------------------------
# WHATSAPP CHAT
# ---------------------------------------------------------------------------

class WhatsAppChat(Base):
    __tablename__ = "whatsapp_chats"

    id: Mapped[int] = mapped_column(primary_key=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), index=True)
    customer_phone: Mapped[str] = mapped_column(String(30), index=True)
    customer_name: Mapped[str] = mapped_column(String(120), default="Customer")
    message_in: Mapped[str] = mapped_column(Text)
    ai_detected_product: Mapped[str | None] = mapped_column(String(160), nullable=True)
    ai_quantity: Mapped[float | None] = mapped_column(Float, nullable=True)
    ai_reply: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), default="inquiry")
    # inquiry | quoted | confirmed | rejected | out_of_stock
    order_id: Mapped[int | None] = mapped_column(ForeignKey("orders.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, index=True)

    business: Mapped["Business"] = relationship(back_populates="whatsapp_chats")


# ---------------------------------------------------------------------------
# TENDER
# ---------------------------------------------------------------------------

class Tender(Base):
    __tablename__ = "tenders"

    id: Mapped[int] = mapped_column(primary_key=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), index=True)
    tender_ref: Mapped[str | None] = mapped_column(String(80), nullable=True)
    title: Mapped[str] = mapped_column(String(300))
    department: Mapped[str] = mapped_column(String(160))
    location: Mapped[str] = mapped_column(String(120))
    state: Mapped[str] = mapped_column(String(80), default="Odisha")
    value_lakhs: Mapped[float] = mapped_column(Float)
    deadline: Mapped[str] = mapped_column(String(30))
    eligibility: Mapped[str] = mapped_column(Text)
    documents_required: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_summary: Mapped[str] = mapped_column(Text)
    source_url: Mapped[str] = mapped_column(String(512))
    is_bookmarked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

    business: Mapped["Business"] = relationship(back_populates="tenders")


# ---------------------------------------------------------------------------
# BUSINESS ALERT
# ---------------------------------------------------------------------------

class BusinessAlert(Base):
    __tablename__ = "business_alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), index=True)
    alert_type: Mapped[str] = mapped_column(String(40), index=True)
    # inventory | payment | sales | expense | opportunity | system
    title: Mapped[str] = mapped_column(String(200))
    message: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(20), default="warning")
    # critical | warning | info | success
    action_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    action_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, index=True)

    business: Mapped["Business"] = relationship(back_populates="alerts")


# ---------------------------------------------------------------------------
# SUBSCRIPTION
# ---------------------------------------------------------------------------

class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    plan: Mapped[str] = mapped_column(String(30), default="free")
    # free | pro | business | enterprise
    billing_cycle: Mapped[str] = mapped_column(String(20), default="monthly")
    # monthly | yearly
    status: Mapped[str] = mapped_column(String(20), default="active")
    # active | cancelled | expired | trial
    amount_paid: Mapped[float] = mapped_column(Float, default=0.0)
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    payment_reference: Mapped[str | None] = mapped_column(String(120), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

    user: Mapped["User"] = relationship(back_populates="subscriptions")


# ---------------------------------------------------------------------------
# AUDIT LOG
# ---------------------------------------------------------------------------

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    business_id: Mapped[int | None] = mapped_column(ForeignKey("businesses.id", ondelete="SET NULL"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(80), index=True)
    # CREATE_ORDER | UPDATE_PRODUCT | DELETE_CUSTOMER | LOGIN | etc.
    entity_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, index=True)

    user: Mapped["User"] = relationship(back_populates="audit_logs")
