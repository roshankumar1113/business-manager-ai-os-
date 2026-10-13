"""
Business Manager — WhatsApp Service
AI-powered product detection, auto-quoting, BUY confirmation → order creation.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from . import models
from .ai_service import call_gemini


# ── Incoming message processor ───────────────────────────────────────────────

def process_message(
    db: Session,
    business: models.Business,
    customer_phone: str,
    customer_name: str,
    message_text: str,
) -> dict:
    """
    Main entry point. Handles:
    1. BUY / CONFIRM → creates order from last quote.
    2. CANCEL / REJECT → marks last quote as rejected.
    3. Product inquiry → Gemini extraction → send quotation.
    4. General message → friendly fallback.
    """
    text_lower = message_text.strip().lower()

    # ── BUY confirmation ──────────────────────────────────────────────────────
    buy_keywords = {"buy", "confirm", "yes", "haan", "ha", "ok", "order",
                    "book", "order kar do", "book it", "confirmed", "proceed"}
    if any(text_lower == kw or text_lower.startswith(kw) for kw in buy_keywords):
        return _confirm_order(db, business, customer_phone, customer_name)

    # ── REJECT / cancel ───────────────────────────────────────────────────────
    reject_keywords = {"no", "nahi", "cancel", "reject", "band karo", "stop"}
    if text_lower in reject_keywords:
        return _reject_quote(db, business, customer_phone, customer_name)

    # ── Product inquiry ───────────────────────────────────────────────────────
    return _process_inquiry(db, business, customer_phone, customer_name, message_text)


# ── Internal helpers ─────────────────────────────────────────────────────────

def _confirm_order(
    db: Session,
    business: models.Business,
    customer_phone: str,
    customer_name: str,
) -> dict:
    last_chat = db.scalar(
        select(models.WhatsAppChat)
        .where(
            models.WhatsAppChat.business_id == business.id,
            models.WhatsAppChat.customer_phone == customer_phone,
            models.WhatsAppChat.status == "quoted",
        )
        .order_by(models.WhatsAppChat.created_at.desc())
    )
    if not last_chat or not last_chat.ai_detected_product:
        reply = (
            f"Namaste {customer_name}! 🙏\n"
            f"I don't see a pending quotation for your account. "
            f"Please send the product name and quantity to get a fresh quote."
        )
        return {"reply": reply, "action": "no_pending_quote"}

    product = db.scalar(
        select(models.Product).where(
            models.Product.business_id == business.id,
            models.Product.name.ilike(f"%{last_chat.ai_detected_product}%"),
            models.Product.is_active == True,
        )
    )
    if not product:
        product = db.scalar(
            select(models.Product).where(
                models.Product.business_id == business.id,
                models.Product.is_active == True,
            )
        )

    if not product:
        return {"reply": "Sorry, that product is currently unavailable.", "action": "product_unavailable"}

    qty = last_chat.ai_quantity or 1.0
    if product.stock_quantity < qty:
        last_chat.status = "out_of_stock"
        db.commit()
        reply = (
            f"Sorry {customer_name}, we only have {product.stock_quantity:g} {product.unit} "
            f"of {product.name} in stock right now.\n"
            f"Would you like to order {product.stock_quantity:g} {product.unit} instead?"
        )
        return {"reply": reply, "action": "out_of_stock"}

    # Get or create customer
    customer = db.scalar(
        select(models.Customer).where(
            models.Customer.business_id == business.id,
            models.Customer.phone == customer_phone,
        )
    )
    if not customer:
        customer = models.Customer(
            business_id=business.id,
            name=customer_name or "WhatsApp Customer",
            phone=customer_phone,
        )
        db.add(customer)
        db.flush()

    subtotal = round(product.selling_price * qty, 2)
    gst = round(subtotal * product.gst_rate / 100, 2)
    cgst = round(gst / 2, 2)
    sgst = round(gst - cgst, 2)
    total = round(subtotal + gst, 2)
    cost = round(product.purchase_price * qty, 2)

    # Deduct stock
    product.stock_quantity -= qty

    # Update customer stats
    customer.total_purchased = round(customer.total_purchased + total, 2)
    customer.pending_amount = round(customer.pending_amount + total, 2)
    customer.last_order_at = datetime.now(timezone.utc)

    invoice_no = f"INV-{datetime.now().strftime('%Y%m%d')}-{int(datetime.now().timestamp()) % 100000:05d}"
    order = models.Order(
        business_id=business.id,
        customer_id=customer.id,
        product_id=product.id,
        quantity=qty,
        unit_price=product.selling_price,
        mrp=product.mrp or product.selling_price,
        discount=0.0,
        taxable_amount=subtotal,
        cgst_amount=cgst,
        sgst_amount=sgst,
        gst_amount=gst,
        total_amount=total,
        cost_amount=cost,
        amount_paid=0.0,
        status="pending",
        channel="whatsapp",
        invoice_no=invoice_no,
        notes=f"WhatsApp order from {customer_phone}",
    )
    db.add(order)
    db.flush()

    last_chat.status = "confirmed"
    last_chat.order_id = order.id
    db.commit()

    reply = (
        f"✅ *Order Confirmed! #{order.id}*\n\n"
        f"Dear {customer.name},\n"
        f"Your order has been placed with *{business.name}*!\n\n"
        f"📦 *{product.name}* — {qty:g} {product.unit}\n"
        f"💰 Total: *₹{total:,.2f}* (incl. GST)\n"
        f"🧾 Invoice No: {invoice_no}\n"
        f"🚚 Delivery: Within 24–48 hours\n"
        f"💳 Payment: Due on delivery\n\n"
        f"Thank you for doing business with us! 🙏"
    )
    return {
        "reply": reply,
        "action": "order_created",
        "order_id": order.id,
        "invoice_no": invoice_no,
        "total_amount": total,
    }


def _reject_quote(
    db: Session,
    business: models.Business,
    customer_phone: str,
    customer_name: str,
) -> dict:
    last_chat = db.scalar(
        select(models.WhatsAppChat)
        .where(
            models.WhatsAppChat.business_id == business.id,
            models.WhatsAppChat.customer_phone == customer_phone,
            models.WhatsAppChat.status == "quoted",
        )
        .order_by(models.WhatsAppChat.created_at.desc())
    )
    if last_chat:
        last_chat.status = "rejected"
        db.commit()

    reply = (
        f"No problem, {customer_name}! 😊\n"
        f"Your quotation has been cancelled.\n"
        f"Feel free to reach out anytime with a new inquiry. We're always here to help!"
    )
    _save_chat(db, business, customer_phone, customer_name, "REJECT", reply, "rejected")
    return {"reply": reply, "action": "quote_rejected"}


def _process_inquiry(
    db: Session,
    business: models.Business,
    customer_phone: str,
    customer_name: str,
    message_text: str,
) -> dict:
    products = list(db.scalars(
        select(models.Product).where(
            models.Product.business_id == business.id,
            models.Product.is_active == True,
        )
    ).all())

    if not products:
        reply = (
            f"Namaste {customer_name}! 🙏 Welcome to *{business.name}*.\n"
            f"We're setting up our product catalog. Please contact us directly for inquiries."
        )
        _save_chat(db, business, customer_phone, customer_name, message_text, reply, "inquiry")
        return {"reply": reply, "action": "no_products"}

    catalog = [
        {"name": p.name, "unit": p.unit, "price": p.selling_price,
         "stock": p.stock_quantity, "gst": p.gst_rate, "category": p.category}
        for p in products
    ]

    # Gemini extraction
    extraction_prompt = (
        f"Product catalog: {json.dumps(catalog)}\n\n"
        f"Customer message: \"{message_text}\"\n\n"
        f"Extract and return ONLY valid raw JSON (no markdown):\n"
        f'{{"is_inquiry": true/false, "product_name": "<best_match_or_null>", '
        f'"quantity": <number_or_null>, "unit": "<string_or_null>"}}'
    )
    raw = call_gemini(extraction_prompt, "You are a product entity extractor for Indian businesses. Return only JSON.", max_tokens=200)

    parsed: dict = {}
    try:
        clean = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        parsed = json.loads(clean)
    except Exception:
        # Keyword fallback
        for p in products:
            if p.name.lower() in message_text.lower() or \
               any(w in message_text.lower() for w in p.name.lower().split() if len(w) > 3):
                parsed = {"is_inquiry": True, "product_name": p.name, "quantity": 1.0, "unit": p.unit}
                break

    # Find best match
    matched = None
    pn = (parsed.get("product_name") or "").lower()
    if pn:
        for p in products:
            if pn in p.name.lower() or p.name.lower() in pn:
                matched = p; break
    if not matched:
        for p in products:
            for word in p.name.lower().split():
                if len(word) > 3 and word in message_text.lower():
                    matched = p; break
            if matched:
                break

    if matched:
        qty = float(parsed.get("quantity") or 1.0)
        subtotal = round(matched.selling_price * qty, 2)
        gst = round(subtotal * matched.gst_rate / 100, 2)
        total = round(subtotal + gst, 2)

        quote = (
            f"Namaste {customer_name}! 🙏\n\n"
            f"Here's your quotation from *{business.name}*:\n\n"
            f"📦 *{matched.name}*\n"
            f"🔢 Quantity: {qty:g} {matched.unit}\n"
            f"💵 Rate: ₹{matched.selling_price:,.2f} / {matched.unit}\n"
            f"📊 GST ({matched.gst_rate:g}%): ₹{gst:,.2f}\n"
            f"💰 *Total: ₹{total:,.2f}*\n"
            f"📦 In Stock: {matched.stock_quantity:g} {matched.unit}\n\n"
            f"Reply *BUY* to place this order instantly.\n"
            f"Reply *REJECT* to cancel."
        )
        chat = models.WhatsAppChat(
            business_id=business.id,
            customer_phone=customer_phone,
            customer_name=customer_name,
            message_in=message_text,
            ai_detected_product=matched.name,
            ai_quantity=qty,
            ai_reply=quote,
            status="quoted",
        )
        db.add(chat); db.commit()
        return {
            "reply": quote, "action": "quotation_sent",
            "detected_product": matched.name, "quantity": qty, "total_amount": total,
        }

    # General fallback
    catalog_preview = ", ".join(p["name"] for p in catalog[:5])
    reply = (
        f"Namaste {customer_name}! 🙏 Welcome to *{business.name}*.\n\n"
        f"We received your message. Our available products include:\n"
        f"📦 {catalog_preview}\n\n"
        f"Please send the product name and quantity for an instant quote!\n"
        f"Example: *'50 bags cement'* or *'100 kg wheat'*"
    )
    _save_chat(db, business, customer_phone, customer_name, message_text, reply, "inquiry")
    return {"reply": reply, "action": "general_reply"}


def _save_chat(db, business, phone, name, msg_in, reply, status):
    db.add(models.WhatsAppChat(
        business_id=business.id, customer_phone=phone,
        customer_name=name, message_in=msg_in, ai_reply=reply, status=status,
    ))
    db.commit()


# ── Payment reminder generator ───────────────────────────────────────────────

def generate_payment_reminder(
    customer_name: str,
    pending_amount: float,
    business_name: str,
    days_overdue: int = 7,
) -> str:
    return (
        f"Namaste *{customer_name} ji*! 🙏\n\n"
        f"This is a gentle reminder from *{business_name}*.\n"
        f"An outstanding balance of *₹{pending_amount:,.2f}* is pending on your account "
        f"({days_overdue} day{'s' if days_overdue != 1 else ''} overdue).\n\n"
        f"Kindly clear this at your earliest convenience to maintain uninterrupted supply.\n\n"
        f"Payment options:\n"
        f"• UPI / Google Pay / PhonePe\n"
        f"• Bank Transfer (NEFT/RTGS)\n"
        f"• Cash payment at our office\n\n"
        f"If you have already paid, please share the reference number.\n"
        f"Thank you for your continued partnership! 🤝\n\n"
        f"— *{business_name}* Team"
    )
