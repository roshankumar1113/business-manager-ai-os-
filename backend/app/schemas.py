"""
Business Manager — Pydantic v2 Schemas
Complete request/response models for all API endpoints.
"""
from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, EmailStr, field_validator


# ── Shared config ────────────────────────────────────────────────────────────
class _ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ── Auth ─────────────────────────────────────────────────────────────────────
class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=6, max_length=128)
    phone: str | None = Field(default=None, max_length=15)

class LoginIn(BaseModel):
    email: str
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    user_name: str
    user_email: str
    plan: str = "free"

class UserOut(_ORM):
    id: int
    name: str
    email: str
    phone: str | None = None
    preferred_language: str
    is_admin: bool
    created_at: datetime

class PasswordChangeIn(BaseModel):
    current_password: str
    new_password: str = Field(min_length=6)


# ── Business ─────────────────────────────────────────────────────────────────
class BusinessIn(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    category: str = "Retail"
    sub_category: str | None = None
    gstin: str | None = None
    pan: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = "Odisha"
    pincode: str | None = None

class BusinessOut(_ORM):
    id: int
    name: str
    category: str
    sub_category: str | None = None
    currency: str
    gstin: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    health_score: int
    whatsapp_connected: bool
    created_at: datetime


# ── Customer ─────────────────────────────────────────────────────────────────
class CustomerIn(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    phone: str | None = None
    email: EmailStr | None = None
    address: str | None = None
    city: str | None = None
    gstin: str | None = None
    notes: str | None = None
    credit_limit: float = Field(default=0.0, ge=0)

class CustomerOut(_ORM):
    id: int
    name: str
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    city: str | None = None
    gstin: str | None = None
    notes: str | None = None
    credit_limit: float
    total_purchased: float
    total_paid: float
    pending_amount: float
    last_order_at: datetime | None = None
    is_active: bool
    created_at: datetime


# ── Product ──────────────────────────────────────────────────────────────────
class ProductIn(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    sku: str | None = None
    barcode: str | None = None
    category: str | None = "General"
    description: str | None = None
    unit: str = "unit"
    purchase_price: float = Field(ge=0)
    selling_price: float = Field(ge=0)
    mrp: float = Field(ge=0, default=0.0)
    stock_quantity: float = Field(ge=0)
    min_stock_level: float = Field(ge=0, default=5.0)
    max_stock_level: float = Field(ge=0, default=1000.0)
    gst_rate: float = Field(ge=0, le=100, default=18.0)
    hsn_code: str | None = None
    supplier_id: int | None = None
    warehouse_location: str | None = None

class ProductOut(_ORM):
    id: int
    name: str
    sku: str | None = None
    barcode: str | None = None
    category: str | None = None
    description: str | None = None
    unit: str
    purchase_price: float
    selling_price: float
    mrp: float
    stock_quantity: float
    min_stock_level: float
    max_stock_level: float
    gst_rate: float
    hsn_code: str | None = None
    supplier_id: int | None = None
    warehouse_location: str | None = None
    is_active: bool
    created_at: datetime

class StockAdjustIn(BaseModel):
    quantity_change: float  # positive = add, negative = deduct
    reason: str = "Manual adjustment"


# ── Order ────────────────────────────────────────────────────────────────────
class OrderIn(BaseModel):
    customer_id: int | None = None
    product_id: int
    quantity: float = Field(gt=0)
    discount: float = Field(ge=0, default=0.0)
    delivery_charge: float = Field(ge=0, default=0.0)
    amount_paid: float = Field(ge=0, default=0.0)
    channel: str = "app"
    notes: str | None = None

class OrderOut(_ORM):
    id: int
    customer_id: int | None = None
    product_id: int
    quantity: float
    unit_price: float
    mrp: float
    discount: float
    taxable_amount: float
    cgst_amount: float
    sgst_amount: float
    gst_amount: float
    total_amount: float
    cost_amount: float
    delivery_charge: float
    amount_paid: float
    status: str
    channel: str
    delivery_status: str
    invoice_no: str | None = None
    notes: str | None = None
    created_at: datetime

class OrderStatusUpdateIn(BaseModel):
    status: str  # paid | partially_paid | cancelled
    amount_paid: float | None = None
    delivery_status: str | None = None


# ── Expense ──────────────────────────────────────────────────────────────────
class ExpenseIn(BaseModel):
    category: str = Field(min_length=1)
    description: str = Field(min_length=1)
    amount: float = Field(gt=0)
    payment_method: str = "cash"
    supplier_id: int | None = None
    notes: str | None = None

class ExpenseOut(_ORM):
    id: int
    category: str
    description: str
    amount: float
    payment_method: str
    supplier_id: int | None = None
    notes: str | None = None
    created_at: datetime


# ── Payment ──────────────────────────────────────────────────────────────────
class PaymentIn(BaseModel):
    order_id: int | None = None
    customer_id: int | None = None
    amount: float = Field(gt=0)
    method: str = "upi"
    reference: str | None = None
    notes: str | None = None

class PaymentOut(_ORM):
    id: int
    order_id: int | None = None
    customer_id: int | None = None
    amount: float
    method: str
    reference: str | None = None
    notes: str | None = None
    created_at: datetime


# ── Supplier ─────────────────────────────────────────────────────────────────
class SupplierIn(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    phone: str | None = None
    email: str | None = None
    category: str | None = "Raw Materials"
    gstin: str | None = None
    pan: str | None = None
    address: str | None = None
    city: str | None = None
    total_purchased: float = Field(ge=0, default=0.0)
    pending_payable: float = Field(ge=0, default=0.0)
    rating: float = Field(ge=1, le=5, default=4.5)
    notes: str | None = None

class SupplierOut(_ORM):
    id: int
    name: str
    phone: str | None = None
    email: str | None = None
    category: str | None = None
    gstin: str | None = None
    address: str | None = None
    city: str | None = None
    total_purchased: float
    pending_payable: float
    rating: float
    notes: str | None = None
    is_active: bool
    created_at: datetime


# ── Project ──────────────────────────────────────────────────────────────────
class ProjectIn(BaseModel):
    name: str = Field(min_length=1)
    client_name: str = Field(min_length=1)
    client_phone: str | None = None
    location: str | None = None
    contract_value: float = Field(ge=0)
    spent_amount: float = Field(ge=0, default=0.0)
    advance_received: float = Field(ge=0, default=0.0)
    status: str = "In Progress"
    start_date: str | None = None
    deadline: str | None = None
    completion_percentage: int = Field(ge=0, le=100, default=0)
    notes: str | None = None

class ProjectOut(_ORM):
    id: int
    name: str
    client_name: str
    client_phone: str | None = None
    location: str | None = None
    contract_value: float
    spent_amount: float
    advance_received: float
    status: str
    start_date: str | None = None
    deadline: str | None = None
    completion_percentage: int
    notes: str | None = None
    created_at: datetime


# ── Quotation ────────────────────────────────────────────────────────────────
class QuotationIn(BaseModel):
    customer_id: int | None = None
    product_id: int
    quantity: float = Field(gt=0)
    discount: float = Field(ge=0, default=0.0)
    delivery_charge: float = Field(ge=0, default=0.0)
    validity_days: int = Field(ge=1, default=15)
    notes: str | None = None

class QuotationOut(_ORM):
    id: int
    customer_id: int | None = None
    product_id: int
    quotation_no: str
    quantity: float
    unit_price: float
    discount: float
    gst_amount: float
    total_amount: float
    validity_days: int
    notes: str | None = None
    status: str
    order_id: int | None = None
    created_at: datetime


# ── WhatsApp ─────────────────────────────────────────────────────────────────
class WhatsAppSimIn(BaseModel):
    customer_phone: str = "9876543210"
    customer_name: str = "Rahul Sharma"
    message_text: str

class WhatsAppChatOut(_ORM):
    id: int
    customer_phone: str
    customer_name: str
    message_in: str
    ai_detected_product: str | None = None
    ai_quantity: float | None = None
    ai_reply: str
    status: str
    order_id: int | None = None
    created_at: datetime

class PaymentReminderIn(BaseModel):
    customer_name: str
    pending_amount: float = Field(gt=0)
    days_overdue: int = Field(ge=0, default=7)
    business_name: str = ""


# ── Dashboard ────────────────────────────────────────────────────────────────
class DashboardOut(BaseModel):
    today_sales: float
    today_expenses: float
    today_estimated_profit: float
    today_orders_count: int
    month_sales: float
    month_expenses: float
    month_estimated_profit: float
    month_orders_count: int
    receivables: float
    pending_orders: int
    low_stock_count: int
    new_customers_this_month: int
    active_projects: int
    health_score: int
    unread_alerts: int


# ── Alert ────────────────────────────────────────────────────────────────────
class AlertOut(_ORM):
    id: int
    alert_type: str
    title: str
    message: str
    severity: str
    action_type: str | None = None
    is_read: bool
    created_at: datetime


# ── Employee ─────────────────────────────────────────────────────────────────
class EmployeeIn(BaseModel):
    name: str = Field(min_length=1)
    phone: str
    role: str = "Salesperson"

class EmployeeOut(_ORM):
    id: int
    name: str
    phone: str
    role: str
    is_active: bool
    created_at: datetime


# ── Reports ──────────────────────────────────────────────────────────────────
class BusinessReportOut(BaseModel):
    period: str
    total_revenue: float
    total_cost_of_goods: float
    total_expenses: float
    gross_profit: float
    estimated_net_profit: float
    profit_margin_pct: float
    total_orders_count: int
    average_order_value: float
    total_receivables: float
    top_selling_products: list[dict]
    expense_breakdown: list[dict]
    top_customers: list[dict]
    monthly_trend: list[dict]


# ── Search ───────────────────────────────────────────────────────────────────
class SearchResultItem(BaseModel):
    type: str
    id: int
    title: str
    subtitle: str
    extra: str | None = None
    meta: dict | None = None


# ── Subscription ─────────────────────────────────────────────────────────────
class SubscriptionOut(_ORM):
    id: int
    plan: str
    billing_cycle: str
    status: str
    amount_paid: float
    started_at: datetime
    expires_at: datetime | None = None


# ── Invoice (virtual — built from Order) ────────────────────────────────────
class InvoiceOut(BaseModel):
    invoice_no: str
    order_id: int
    business_name: str
    business_address: str | None = None
    business_gstin: str | None = None
    business_phone: str | None = None
    customer_name: str
    customer_address: str | None = None
    customer_gstin: str | None = None
    customer_phone: str | None = None
    product_name: str
    product_hsn: str | None = None
    quantity: float
    unit: str
    unit_price: float
    discount: float
    taxable_amount: float
    gst_rate: float
    cgst_amount: float
    sgst_amount: float
    gst_amount: float
    delivery_charge: float
    total_amount: float
    amount_paid: float
    balance_due: float
    status: str
    channel: str
    invoice_date: str
    payment_terms: str = "Due on delivery"
