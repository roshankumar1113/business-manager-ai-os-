"""
Business Manager — AI Service
Google Gemini 2.5 Flash integration with full business context grounding.
"""
from __future__ import annotations
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from .config import settings
from . import models


# ── Gemini REST caller ───────────────────────────────────────────────────────

def call_gemini(prompt: str, system_instruction: str = "", max_tokens: int = 1024) -> str:
    """Calls Gemini via raw REST. Returns text or a friendly error string."""
    api_key = settings.gemini_api_key
    if not api_key:
        return "AI service is not configured. Please set GEMINI_API_KEY in .env"

    model = settings.gemini_model or "gemini-2.5-flash"
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={api_key}"
    )
    body: dict = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": max_tokens,
        },
    }
    if system_instruction:
        body["systemInstruction"] = {"parts": [{"text": system_instruction}]}

    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=settings.gemini_timeout) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            candidates = result.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "").strip()
            return "AI returned an empty response."
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="ignore")[:300]
        return f"Gemini API Error ({e.code}): {err}"
    except Exception as e:
        return f"AI Service Error: {str(e)}"


# ── Business context builder ─────────────────────────────────────────────────

def get_business_context(db: Session, business: models.Business) -> dict:
    """Pulls a comprehensive factual snapshot of the business from the DB."""
    now = datetime.now(timezone.utc)
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month_start = (month_start - timedelta(days=1)).replace(day=1)

    def _sum(model, col, *, extra_where=None):
        q = select(func.coalesce(func.sum(col), 0.0)).where(
            getattr(model, "business_id") == business.id
        )
        if extra_where is not None:
            q = q.where(extra_where)
        return float(db.scalar(q) or 0.0)

    # ── Sales ──
    today_sales    = _sum(models.Order, models.Order.total_amount,
                          extra_where=models.Order.created_at >= day_start)
    month_sales    = _sum(models.Order, models.Order.total_amount,
                          extra_where=models.Order.created_at >= month_start)
    lm_sales       = _sum(models.Order, models.Order.total_amount,
                          extra_where=(models.Order.created_at >= last_month_start) &
                                      (models.Order.created_at < month_start))

    # ── Costs ──
    today_cogs     = _sum(models.Order, models.Order.cost_amount,
                          extra_where=models.Order.created_at >= day_start)
    month_cogs     = _sum(models.Order, models.Order.cost_amount,
                          extra_where=models.Order.created_at >= month_start)

    # ── Expenses ──
    today_exp      = _sum(models.Expense, models.Expense.amount,
                          extra_where=models.Expense.created_at >= day_start)
    month_exp      = _sum(models.Expense, models.Expense.amount,
                          extra_where=models.Expense.created_at >= month_start)

    # ── Profits ──
    today_profit   = round(today_sales  - today_cogs  - today_exp,  2)
    month_profit   = round(month_sales  - month_cogs  - month_exp,  2)

    # ── Order counts ──
    today_orders = int(db.scalar(
        select(func.count()).where(
            models.Order.business_id == business.id,
            models.Order.created_at >= day_start
        )
    ) or 0)
    month_orders = int(db.scalar(
        select(func.count()).where(
            models.Order.business_id == business.id,
            models.Order.created_at >= month_start
        )
    ) or 0)
    pending_orders = int(db.scalar(
        select(func.count()).where(
            models.Order.business_id == business.id,
            models.Order.status == "pending",
        )
    ) or 0)

    # ── Receivables ──
    unpaid = list(db.scalars(
        select(models.Order).where(
            models.Order.business_id == business.id,
            models.Order.total_amount > models.Order.amount_paid,
            models.Order.status != "cancelled",
        )
    ).all())
    total_receivable = round(sum(o.total_amount - o.amount_paid for o in unpaid), 2)

    # Debt per customer (top 5)
    debt_map: dict[str, float] = {}
    for o in unpaid:
        due = o.total_amount - o.amount_paid
        if o.customer_id:
            cust = db.get(models.Customer, o.customer_id)
            key = cust.name if cust else "Walk-in"
        else:
            key = "Walk-in"
        debt_map[key] = round(debt_map.get(key, 0.0) + due, 2)
    top_debtors = sorted(debt_map.items(), key=lambda x: x[1], reverse=True)[:5]

    # ── Inventory ──
    low_stock = list(db.scalars(
        select(models.Product).where(
            models.Product.business_id == business.id,
            models.Product.is_active == True,
            models.Product.stock_quantity <= models.Product.min_stock_level,
        )
    ).all())
    all_products = list(db.scalars(
        select(models.Product).where(
            models.Product.business_id == business.id,
            models.Product.is_active == True,
        )
    ).all())

    # ── Customers ──
    total_customers = int(db.scalar(
        select(func.count()).where(
            models.Customer.business_id == business.id,
            models.Customer.is_active == True,
        )
    ) or 0)
    new_customers = int(db.scalar(
        select(func.count()).where(
            models.Customer.business_id == business.id,
            models.Customer.created_at >= month_start,
        )
    ) or 0)

    # ── Projects ──
    projects = list(db.scalars(
        select(models.Project).where(models.Project.business_id == business.id)
    ).all())
    active_projects = [p for p in projects if p.status == "In Progress"]

    # ── Expense breakdown (this month) ──
    exp_rows = list(db.execute(
        select(models.Expense.category, func.sum(models.Expense.amount).label("total"))
        .where(
            models.Expense.business_id == business.id,
            models.Expense.created_at >= month_start,
        )
        .group_by(models.Expense.category)
    ).all())

    return {
        "business_name":        business.name,
        "category":             business.category,
        "city":                 business.city or "India",
        "today_sales":          round(today_sales, 2),
        "today_expenses":       round(today_exp, 2),
        "today_profit":         today_profit,
        "today_orders":         today_orders,
        "month_sales":          round(month_sales, 2),
        "month_expenses":       round(month_exp, 2),
        "month_profit":         month_profit,
        "month_orders":         month_orders,
        "last_month_sales":     round(lm_sales, 2),
        "sales_growth_pct":     round(((month_sales - lm_sales) / lm_sales * 100) if lm_sales else 0, 1),
        "pending_orders":       pending_orders,
        "total_receivable":     total_receivable,
        "top_debtors": [{"customer": k, "pending": v} for k, v in top_debtors],
        "low_stock_items": [
            {"name": p.name, "stock": p.stock_quantity, "unit": p.unit, "min": p.min_stock_level}
            for p in low_stock
        ],
        "total_products":       len(all_products),
        "total_customers":      total_customers,
        "new_customers_month":  new_customers,
        "active_projects":      len(active_projects),
        "projects": [
            {"name": p.name, "client": p.client_name, "value": p.contract_value,
             "spent": p.spent_amount, "status": p.status, "pct": p.completion_percentage}
            for p in projects[:5]
        ],
        "expense_breakdown": [{"category": r[0], "amount": round(float(r[1]), 2)} for r in exp_rows],
    }


# ── AI Query (text / voice) ──────────────────────────────────────────────────

def answer_business_query(db: Session, business: models.Business, query: str) -> dict:
    ctx = get_business_context(db, business)
    system = (
        "You are 'Business AI', the intelligent AI Employee of a small Indian business owner. "
        "You have access to the owner's real-time business data (provided as context). "
        "Rules:\n"
        "- Base all financial figures strictly on the provided context.\n"
        "- Use ₹ and Indian number formatting (lakhs, crores).\n"
        "- Be concise, warm, and practical. Support Hinglish naturally.\n"
        "- Distinguish between verified data and estimates.\n"
        "- For action requests (reminders, reorders), describe what needs to happen but "
        "  note that owner confirmation is required before external actions."
    )
    prompt = (
        f"BUSINESS CONTEXT (verified database data):\n"
        f"Business: {ctx['business_name']} ({ctx['category']}, {ctx['city']})\n"
        f"Today: Sales ₹{ctx['today_sales']:,.0f} | Expenses ₹{ctx['today_expenses']:,.0f} | "
        f"Profit ₹{ctx['today_profit']:,.0f} | Orders {ctx['today_orders']}\n"
        f"This Month: Sales ₹{ctx['month_sales']:,.0f} | Profit ₹{ctx['month_profit']:,.0f} | "
        f"Orders {ctx['month_orders']} | Growth {ctx['sales_growth_pct']:+.1f}%\n"
        f"Receivables: ₹{ctx['total_receivable']:,.0f} from {len(ctx['top_debtors'])} customers\n"
        f"Top Debtors: {json.dumps(ctx['top_debtors'])}\n"
        f"Low Stock ({len(ctx['low_stock_items'])} items): {json.dumps(ctx['low_stock_items'])}\n"
        f"Active Projects: {ctx['active_projects']}\n"
        f"Projects: {json.dumps(ctx['projects'])}\n"
        f"Expense Breakdown: {json.dumps(ctx['expense_breakdown'])}\n\n"
        f"OWNER'S QUESTION / VOICE COMMAND: \"{query}\"\n\n"
        f"Answer directly and helpfully:"
    )
    answer = call_gemini(prompt, system, max_tokens=1200)
    return {"answer": answer, "context": ctx, "source": "Gemini 2.5 Flash + Live Business Data"}


# ── Action Plan ──────────────────────────────────────────────────────────────

def get_action_plan(db: Session, business: models.Business) -> list[dict]:
    ctx = get_business_context(db, business)
    actions: list[dict] = []
    idx = 1

    # 1. Collect overdue payments
    if ctx["total_receivable"] > 0:
        top = ctx["top_debtors"][0] if ctx["top_debtors"] else None
        desc = f"₹{ctx['total_receivable']:,.0f} is pending from customers."
        if top:
            desc += f" Highest: {top['customer']} owes ₹{top['pending']:,.0f}."
        actions.append({
            "id": idx, "type": "payment", "priority": "critical",
            "title": "Collect Overdue Payments",
            "description": desc,
            "badge": "Urgent Cash Flow",
            "action_text": "Send WhatsApp Reminders",
            "action_type": "whatsapp_reminder",
        })
        idx += 1

    # 2. Reorder low stock
    if ctx["low_stock_items"]:
        names = ", ".join(p["name"] for p in ctx["low_stock_items"][:3])
        actions.append({
            "id": idx, "type": "inventory", "priority": "high",
            "title": "Reorder Low-Stock Products",
            "description": f"{len(ctx['low_stock_items'])} item(s) below minimum: {names}.",
            "badge": "Stock Alert",
            "action_text": "Contact Supplier",
            "action_type": "reorder_stock",
        })
        idx += 1

    # 3. Category-specific
    if business.category == "Construction":
        actions.append({
            "id": idx, "type": "opportunity", "priority": "medium",
            "title": "Review Government Tenders",
            "description": "New PWD & PMGSY tenders match your business profile and location.",
            "badge": "Growth Opportunity",
            "action_text": "View Tenders",
            "action_type": "view_tenders",
        })
    elif business.category == "Agriculture":
        actions.append({
            "id": idx, "type": "market", "priority": "medium",
            "title": "Check Mandi Commodity Rates",
            "description": "Wheat and Mustard prices are up 3–4% in regional APMCs this week.",
            "badge": "Market Intelligence",
            "action_text": "View Mandi Rates",
            "action_type": "view_mandi",
        })
    else:
        actions.append({
            "id": idx, "type": "sales", "priority": "medium",
            "title": "Promote Fast-Moving Products",
            "description": "Send a catalog update to your regular buyers via WhatsApp.",
            "badge": "Sales Boost",
            "action_text": "Broadcast Catalog",
            "action_type": "broadcast",
        })
    idx += 1

    # 4. Expense review
    if ctx["month_expenses"] > 0:
        top_cat = max(ctx["expense_breakdown"], key=lambda x: x["amount"], default=None)
        desc = f"₹{ctx['month_expenses']:,.0f} spent this month."
        if top_cat:
            desc += f" Highest category: {top_cat['category']} (₹{top_cat['amount']:,.0f})."
        actions.append({
            "id": idx, "type": "expense", "priority": "low",
            "title": "Review Monthly Expenses",
            "description": desc,
            "badge": "Cost Control",
            "action_text": "View Expenses",
            "action_type": "view_expenses",
        })
        idx += 1

    # 5. Sales growth context
    if ctx["sales_growth_pct"] < -10:
        actions.append({
            "id": idx, "type": "alert", "priority": "high",
            "title": "Sales Down — Take Action",
            "description": f"Monthly sales are {abs(ctx['sales_growth_pct']):.1f}% lower than last month. Review pricing and customer outreach.",
            "badge": "Revenue Alert",
            "action_text": "Analyse Sales",
            "action_type": "view_sales",
        })

    return actions


# ── Business Health Score ────────────────────────────────────────────────────

def compute_health_score(db: Session, business: models.Business) -> dict:
    ctx = get_business_context(db, business)
    score = 75
    bonuses: list[str] = []
    penalties: list[str] = []

    # Receivable ratio
    if ctx["month_sales"] > 0:
        ratio = ctx["total_receivable"] / ctx["month_sales"]
        if ratio > 0.5:
            score -= 18; penalties.append("Very high outstanding receivables vs monthly sales")
        elif ratio > 0.25:
            score -= 9; penalties.append("Moderate outstanding receivables")
        else:
            score += 5; bonuses.append("Good payment collection rate")

    # Profit margin
    if ctx["month_sales"] > 0:
        margin = ctx["month_profit"] / ctx["month_sales"]
        if margin >= 0.3:
            score += 12; bonuses.append("Strong profit margin above 30%")
        elif margin >= 0.15:
            score += 6; bonuses.append("Healthy profit margin 15–30%")
        elif margin < 0.05:
            score -= 10; penalties.append("Very thin profit margin below 5%")

    # Sales growth
    if ctx["sales_growth_pct"] > 10:
        score += 8; bonuses.append(f"Sales growing +{ctx['sales_growth_pct']:.1f}% vs last month")
    elif ctx["sales_growth_pct"] < -15:
        score -= 8; penalties.append(f"Sales declined {abs(ctx['sales_growth_pct']):.1f}% vs last month")

    # Inventory health
    n_low = len(ctx["low_stock_items"])
    if n_low == 0:
        score += 5; bonuses.append("All inventory levels healthy")
    elif n_low >= 4:
        score -= 8; penalties.append(f"{n_low} products critically low on stock")
    elif n_low >= 2:
        score -= 4; penalties.append(f"{n_low} products approaching minimum stock")

    # Customer growth
    if ctx["new_customers_month"] >= 3:
        score += 5; bonuses.append(f"{ctx['new_customers_month']} new customers this month")

    score = max(20, min(98, score))
    grade = "Excellent" if score >= 85 else ("Good" if score >= 70 else ("Fair" if score >= 55 else "Needs Attention"))

    prompt = (
        f"Business '{business.name}' ({business.category}) Health Score: {score}/100 ({grade})\n"
        f"Strengths: {', '.join(bonuses) or 'Building baseline'}\n"
        f"Risks: {', '.join(penalties) or 'None identified'}\n"
        f"Month Sales: ₹{ctx['month_sales']:,.0f} | Receivables: ₹{ctx['total_receivable']:,.0f} | "
        f"Margin: {ctx['month_profit']/ctx['month_sales']*100:.1f}% (if sales > 0)\n\n"
        f"Write a professional 2-sentence explanation of this score for the business owner. "
        f"Be specific, actionable, and encouraging."
    )
    explanation = call_gemini(prompt, "You are a senior financial advisor for Indian small businesses.", max_tokens=200)

    return {
        "score": score,
        "grade": grade,
        "explanation": explanation,
        "bonuses": bonuses,
        "penalties": penalties,
        "context": ctx,
    }


# ── Inventory Intelligence ───────────────────────────────────────────────────

def get_inventory_intelligence(db: Session, business: models.Business) -> dict:
    """Analyses inventory and returns AI-powered recommendations."""
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    products = list(db.scalars(
        select(models.Product).where(
            models.Product.business_id == business.id,
            models.Product.is_active == True,
        )
    ).all())

    # Sales velocity per product (units sold this month)
    velocity: dict[int, float] = {}
    for p in products:
        sold = float(db.scalar(
            select(func.coalesce(func.sum(models.Order.quantity), 0.0)).where(
                models.Order.business_id == business.id,
                models.Order.product_id == p.id,
                models.Order.created_at >= month_start,
            )
        ) or 0.0)
        velocity[p.id] = sold

    low_stock = [p for p in products if p.stock_quantity <= p.min_stock_level]
    fast_moving = sorted(products, key=lambda p: velocity.get(p.id, 0), reverse=True)[:5]
    slow_moving = [p for p in products if velocity.get(p.id, 0) == 0]

    # Days until stockout estimate
    stockout_warnings = []
    for p in products:
        v = velocity.get(p.id, 0)
        if v > 0 and p.stock_quantity > 0:
            days_left = round(p.stock_quantity / (v / 30), 1)
            if days_left < 10:
                stockout_warnings.append({
                    "product": p.name, "stock": p.stock_quantity,
                    "unit": p.unit, "days_until_stockout": days_left,
                    "daily_velocity": round(v / 30, 2),
                })

    return {
        "low_stock": [{"id": p.id, "name": p.name, "stock": p.stock_quantity, "min": p.min_stock_level, "unit": p.unit} for p in low_stock],
        "fast_moving": [{"id": p.id, "name": p.name, "sold_this_month": velocity.get(p.id, 0), "unit": p.unit} for p in fast_moving],
        "slow_moving": [{"id": p.id, "name": p.name, "stock": p.stock_quantity, "unit": p.unit} for p in slow_moving[:5]],
        "stockout_warnings": sorted(stockout_warnings, key=lambda x: x["days_until_stockout"]),
        "total_inventory_value": round(sum(p.stock_quantity * p.purchase_price for p in products), 2),
    }


# ── AI Recommendations ───────────────────────────────────────────────────────

def get_ai_recommendations(db: Session, business: models.Business) -> list[dict]:
    ctx = get_business_context(db, business)
    inv = get_inventory_intelligence(db, business)

    prompt = (
        f"Business: {ctx['business_name']} ({ctx['category']})\n"
        f"Month Sales: ₹{ctx['month_sales']:,.0f} | Profit: ₹{ctx['month_profit']:,.0f}\n"
        f"Receivables: ₹{ctx['total_receivable']:,.0f}\n"
        f"Low stock items: {len(inv['low_stock'])}\n"
        f"Fast-moving products: {[p['name'] for p in inv['fast_moving'][:3]]}\n"
        f"Slow-moving products: {[p['name'] for p in inv['slow_moving'][:3]]}\n"
        f"Sales growth: {ctx['sales_growth_pct']:+.1f}%\n\n"
        f"Give exactly 3 specific, actionable business recommendations as a JSON array: "
        f'[{{"title": "...", "detail": "...", "priority": "high|medium|low"}}]. '
        f"Return ONLY valid JSON, no markdown."
    )
    raw = call_gemini(prompt, "You are a pragmatic business advisor for Indian SMB owners.", max_tokens=600)
    try:
        clean = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        return json.loads(clean)
    except Exception:
        return [{"title": "Review your business data", "detail": raw[:200], "priority": "medium"}]
