"""
Business Manager — Rich Demo Data Seeder
Creates a demo user with 3 businesses (Construction, Agriculture, Retail)
and comprehensive data: products, customers, orders, expenses, payments,
projects, suppliers, quotations, and business alerts.
"""
from __future__ import annotations
import sys
import os
from datetime import datetime, timezone, timedelta
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine
from app.models import Base, User, Business, Customer, Product, Order, Expense, Payment, Project, Supplier, Quotation, BusinessAlert, Subscription, WhatsAppChat
from app.security import hash_password

def now(): return datetime.now(timezone.utc)
def days_ago(n): return now() - timedelta(days=n)
def rnd(a, b): return round(random.uniform(a, b), 2)


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Check if already seeded
        existing = db.query(User).filter_by(email="demo@businessmanager.local").first()
        if existing:
            print("✅ Demo data already seeded.")
            return

        print("🌱 Seeding demo data...")

        # ── Demo User ────────────────────────────────────────────────────────
        user = User(
            name="Rajesh Kumar Sharma",
            email="demo@businessmanager.local",
            phone="+91 98765 43210",
            password_hash=hash_password("DemoPass123!"),
            is_active=True,
            preferred_language="en",
        )
        db.add(user)
        db.flush()

        db.add(Subscription(user_id=user.id, plan="pro", status="active"))

        # ════════════════════════════════════════════════════════════════════
        # BUSINESS 1: Construction
        # ════════════════════════════════════════════════════════════════════
        biz_c = Business(
            owner_id=user.id, name="Sharma Construction & Contractors",
            category="Construction", gstin="21AABCS1429B1ZB",
            phone="+91 98765 43210", address="Plot No. 45, Industrial Area",
            city="Bhubaneswar", state="Odisha", pincode="751010",
            health_score=78,
        )
        db.add(biz_c); db.flush()

        # Suppliers — Construction
        sup_c1 = Supplier(business_id=biz_c.id, name="Odisha Steel Traders", phone="9437001122",
                          category="Steel", city="Bhubaneswar", total_purchased=485000, pending_payable=75000, rating=4.5)
        sup_c2 = Supplier(business_id=biz_c.id, name="UltraTech Cement Depot", phone="9437003344",
                          category="Cement", city="Cuttack", total_purchased=320000, pending_payable=42000, rating=4.8)
        sup_c3 = Supplier(business_id=biz_c.id, name="Ravi Sand & Aggregate", phone="9437005566",
                          category="Aggregate", city="Bhubaneswar", total_purchased=95000, pending_payable=12000, rating=4.2)
        db.add_all([sup_c1, sup_c2, sup_c3]); db.flush()

        # Products — Construction
        prods_c = [
            Product(business_id=biz_c.id, name="OPC 53 Grade Cement", category="Cement",
                    unit="bag", purchase_price=340, selling_price=375, mrp=390,
                    stock_quantity=420, min_stock_level=100, gst_rate=28, hsn_code="2523",
                    supplier_id=sup_c2.id, warehouse_location="Godown A"),
            Product(business_id=biz_c.id, name="TMT Steel 500D (12mm)", category="Steel",
                    unit="ton", purchase_price=51500, selling_price=56000, mrp=58000,
                    stock_quantity=18.5, min_stock_level=5, gst_rate=18, hsn_code="7213",
                    supplier_id=sup_c1.id, warehouse_location="Yard B"),
            Product(business_id=biz_c.id, name="River Sand (Coarse)", category="Aggregate",
                    unit="cu.ft", purchase_price=44, selling_price=55, mrp=60,
                    stock_quantity=1200, min_stock_level=300, gst_rate=5, hsn_code="2505",
                    supplier_id=sup_c3.id),
            Product(business_id=biz_c.id, name="Fly Ash Bricks (1000 pcs)", category="Bricks",
                    unit="batch", purchase_price=5200, selling_price=5800, mrp=6200,
                    stock_quantity=35, min_stock_level=10, gst_rate=5, hsn_code="6904"),
            Product(business_id=biz_c.id, name="PVC Pipes (4-inch, 3m)", category="Plumbing",
                    unit="piece", purchase_price=185, selling_price=220, mrp=250,
                    stock_quantity=85, min_stock_level=20, gst_rate=18, hsn_code="3917"),
            Product(business_id=biz_c.id, name="Plywood 18mm (8×4 ft)", category="Wood",
                    unit="sheet", purchase_price=1850, selling_price=2150, mrp=2400,
                    stock_quantity=12, min_stock_level=15, gst_rate=18, hsn_code="4412"),
        ]
        db.add_all(prods_c); db.flush()

        # Customers — Construction
        custs_c = [
            Customer(business_id=biz_c.id, name="Pooja Housing Works", phone="9437011111",
                     city="Bhubaneswar", total_purchased=185000, total_paid=167772, pending_amount=17228),
            Customer(business_id=biz_c.id, name="Bijay Kumar (Contractor)", phone="9437022222",
                     city="Cuttack", total_purchased=92500, total_paid=82500, pending_amount=10000),
            Customer(business_id=biz_c.id, name="Sambalpur Infra Pvt Ltd", phone="9437033333",
                     city="Sambalpur", gstin="21AASCS4500B1ZA",
                     total_purchased=320000, total_paid=280000, pending_amount=40000),
            Customer(business_id=biz_c.id, name="Rajan Singh (Site)", phone="9437044444",
                     city="Rourkela", total_purchased=45000, total_paid=45000, pending_amount=0),
        ]
        db.add_all(custs_c); db.flush()

        # Orders — Construction (spread over last 45 days)
        cement = prods_c[0]; steel = prods_c[1]; sand = prods_c[2]
        for i, (qty, prod, cust, paid_frac, ch, days) in enumerate([
            (100, cement, custs_c[0], 0.9, "app", 2),
            (5, steel, custs_c[2], 1.0, "app", 5),
            (500, sand, custs_c[1], 0.85, "whatsapp", 8),
            (50, cement, custs_c[3], 1.0, "app", 10),
            (2.5, steel, custs_c[0], 0.7, "app", 15),
            (200, sand, custs_c[2], 1.0, "whatsapp", 18),
            (80, cement, custs_c[1], 1.0, "app", 22),
            (3, steel, custs_c[2], 0.8, "voice", 28),
            (150, cement, custs_c[0], 0.6, "app", 35),
            (120, cement, custs_c[2], 1.0, "app", 40),
        ]):
            sub = round(prod.selling_price * qty, 2)
            gst = round(sub * prod.gst_rate / 100, 2)
            total = round(sub + gst, 2)
            paid = round(total * paid_frac, 2)
            status = "paid" if paid >= total else ("partially_paid" if paid > 0 else "pending")
            o = Order(
                business_id=biz_c.id, customer_id=cust.id, product_id=prod.id,
                quantity=qty, unit_price=prod.selling_price, mrp=prod.mrp or prod.selling_price,
                discount=0, taxable_amount=sub, cgst_amount=round(gst/2, 2),
                sgst_amount=round(gst - round(gst/2, 2), 2), gst_amount=gst,
                total_amount=total, cost_amount=round(prod.purchase_price * qty, 2),
                amount_paid=paid, status=status, channel=ch,
                invoice_no=f"INV-{datetime.now().strftime('%Y%m%d')}-C{i+1:03d}",
                created_at=days_ago(days),
            )
            db.add(o)
        db.flush()

        # Expenses — Construction
        for cat, desc, amt, d in [
            ("Labour",    "Site labour wages — 12 workers",   28000, 1),
            ("Transport", "Material delivery — 3 trips",       8500, 3),
            ("Fuel",      "JCB machine diesel",                4200, 5),
            ("Labour",    "Skilled mason — plastering work",  15000, 8),
            ("Transport", "Steel delivery from Bhubaneswar",   6500, 12),
            ("Maintenance","Mixer machine repair",             3800, 15),
            ("Labour",    "Site labour — foundation digging",  22000, 20),
            ("Rent",      "Office rent - October",             8000, 25),
            ("Fuel",      "Generator diesel for site",         3200, 30),
            ("Marketing", "Newspaper advertisement",           5000, 35),
        ]:
            db.add(Expense(business_id=biz_c.id, category=cat, description=desc,
                           amount=amt, created_at=days_ago(d)))

        # Projects
        projects = [
            Project(business_id=biz_c.id, name="PMGSY Rural Road — Baripada Block",
                    client_name="Rural Works Department, Odisha", client_phone="06792-250123",
                    location="Baripada, Mayurbhanj", contract_value=4850000, spent_amount=2100000,
                    advance_received=970000, status="In Progress", start_date="2026-06-15",
                    deadline="2026-12-31", completion_percentage=43),
            Project(business_id=biz_c.id, name="Residential Complex G+3 — Cuttack",
                    client_name="Sambalpur Infra Pvt Ltd", client_phone="9437033333",
                    location="Cuttack", contract_value=3200000, spent_amount=1980000,
                    advance_received=800000, status="In Progress", start_date="2026-04-01",
                    deadline="2027-03-31", completion_percentage=62),
            Project(business_id=biz_c.id, name="School Building Renovation — Dhenkanal",
                    client_name="Dhenkanal Municipal Corporation", client_phone="06762-225001",
                    location="Dhenkanal", contract_value=1250000, spent_amount=1250000,
                    advance_received=1250000, status="Completed", start_date="2026-01-10",
                    deadline="2026-05-30", completion_percentage=100),
        ]
        db.add_all(projects)

        # Alerts
        db.add(BusinessAlert(business_id=biz_c.id, alert_type="payment", severity="critical",
                             title="₹17,228 overdue from Pooja Housing Works",
                             message="Payment of ₹17,228 is overdue. Customer last paid 22 days ago. Send reminder.",
                             action_type="whatsapp_reminder"))
        db.add(BusinessAlert(business_id=biz_c.id, alert_type="inventory", severity="warning",
                             title="Plywood 18mm stock below minimum",
                             message="Only 12 sheets in stock (minimum: 15). Reorder from supplier soon.",
                             action_type="reorder_stock"))
        db.add(BusinessAlert(business_id=biz_c.id, alert_type="opportunity", severity="info",
                             title="New tender match: PWD Road Contract — ₹48.5 Lakh",
                             message="PMGSY Phase-IV road tender in Mayurbhanj matches your business profile.",
                             action_type="view_tenders"))

        # ════════════════════════════════════════════════════════════════════
        # BUSINESS 2: Agriculture
        # ════════════════════════════════════════════════════════════════════
        biz_a = Business(
            owner_id=user.id, name="Sharma Agro & Fertilizer Store",
            category="Agriculture", gstin="21AABCS1429B2ZC",
            phone="+91 98765 43211", address="Main Market Road, Village Sundergarh",
            city="Sundergarh", state="Odisha", pincode="770001",
            health_score=82,
        )
        db.add(biz_a); db.flush()

        sup_a1 = Supplier(business_id=biz_a.id, name="Coromandel Fertilizers Depot", phone="9437100001",
                          category="Fertilizers", city="Bhubaneswar", total_purchased=280000, pending_payable=38000, rating=4.7)
        sup_a2 = Supplier(business_id=biz_a.id, name="National Seeds Corporation", phone="9437100002",
                          category="Seeds", city="Sambalpur", total_purchased=95000, pending_payable=15000, rating=4.3)
        db.add_all([sup_a1, sup_a2]); db.flush()

        prods_a = [
            Product(business_id=biz_a.id, name="DAP Fertilizer (50kg bag)", category="Fertilizers",
                    unit="bag", purchase_price=1200, selling_price=1350, mrp=1380,
                    stock_quantity=280, min_stock_level=50, gst_rate=5, hsn_code="3102",
                    supplier_id=sup_a1.id),
            Product(business_id=biz_a.id, name="Urea (45kg bag)", category="Fertilizers",
                    unit="bag", purchase_price=245, selling_price=266, mrp=275,
                    stock_quantity=420, min_stock_level=100, gst_rate=0, hsn_code="3102",
                    supplier_id=sup_a1.id),
            Product(business_id=biz_a.id, name="Paddy Seeds HB-1 (5kg)", category="Seeds",
                    unit="packet", purchase_price=380, selling_price=440, mrp=460,
                    stock_quantity=85, min_stock_level=20, gst_rate=0, hsn_code="1006",
                    supplier_id=sup_a2.id),
            Product(business_id=biz_a.id, name="Pesticide — Chlorpyrifos 20EC (500ml)", category="Pesticides",
                    unit="bottle", purchase_price=165, selling_price=195, mrp=210,
                    stock_quantity=38, min_stock_level=20, gst_rate=18, hsn_code="3808"),
            Product(business_id=biz_a.id, name="Potash (MOP 50kg bag)", category="Fertilizers",
                    unit="bag", purchase_price=920, selling_price=1050, mrp=1100,
                    stock_quantity=18, min_stock_level=25, gst_rate=5, hsn_code="3104",
                    supplier_id=sup_a1.id),
            Product(business_id=biz_a.id, name="Farm Equipment — Manual Sprayer (16L)", category="Equipment",
                    unit="piece", purchase_price=850, selling_price=1100, mrp=1200,
                    stock_quantity=12, min_stock_level=5, gst_rate=12, hsn_code="8424"),
        ]
        db.add_all(prods_a); db.flush()

        custs_a = [
            Customer(business_id=biz_a.id, name="Suresh Patel (Farmer)", phone="9437200001",
                     city="Sundergarh", total_purchased=28500, total_paid=25000, pending_amount=3500),
            Customer(business_id=biz_a.id, name="Mohan Mahato (Farmer)", phone="9437200002",
                     city="Rourkela", total_purchased=42000, total_paid=42000, pending_amount=0),
            Customer(business_id=biz_a.id, name="Kisan Cooperative Society", phone="9437200003",
                     city="Sundergarh", gstin="21AAKCS0001A1ZK",
                     total_purchased=185000, total_paid=155000, pending_amount=30000),
            Customer(business_id=biz_a.id, name="Ramesh Nayak (Farmer)", phone="9437200004",
                     city="Jharsuguda", total_purchased=18000, total_paid=18000, pending_amount=0),
        ]
        db.add_all(custs_a); db.flush()

        dap = prods_a[0]; urea = prods_a[1]; seeds = prods_a[2]
        for i, (qty, prod, cust, paid_frac, ch, d) in enumerate([
            (50, dap,  custs_a[2], 1.0, "app", 1),
            (100, urea, custs_a[0], 0.88, "whatsapp", 4),
            (20, seeds, custs_a[1], 1.0, "app", 7),
            (80, dap,  custs_a[2], 1.0, "app", 12),
            (30, urea, custs_a[3], 1.0, "whatsapp", 16),
            (15, seeds, custs_a[0], 0.7, "app", 21),
            (60, dap,  custs_a[1], 1.0, "app", 25),
            (120, urea, custs_a[2], 0.85, "app", 30),
        ]):
            sub = round(prod.selling_price * qty, 2)
            gst = round(sub * prod.gst_rate / 100, 2)
            total = round(sub + gst, 2)
            paid = round(total * paid_frac, 2)
            status = "paid" if paid >= total else "partially_paid" if paid > 0 else "pending"
            db.add(Order(
                business_id=biz_a.id, customer_id=cust.id, product_id=prod.id,
                quantity=qty, unit_price=prod.selling_price, mrp=prod.mrp or prod.selling_price,
                discount=0, taxable_amount=sub, cgst_amount=round(gst/2, 2),
                sgst_amount=round(gst - round(gst/2, 2), 2), gst_amount=gst,
                total_amount=total, cost_amount=round(prod.purchase_price * qty, 2),
                amount_paid=paid, status=status, channel=ch,
                invoice_no=f"INV-{datetime.now().strftime('%Y%m%d')}-A{i+1:03d}",
                created_at=days_ago(d),
            ))

        for cat, desc, amt, d in [
            ("Transport", "Fertilizer delivery to villages", 3500, 2),
            ("Labour",    "Loading/unloading workers",        2800, 6),
            ("Rent",      "Warehouse rent — October",         6000, 10),
            ("Electricity", "Cold storage electricity bill",  2200, 15),
            ("Marketing", "Seasonal crop advisory pamphlets", 1800, 20),
        ]:
            db.add(Expense(business_id=biz_a.id, category=cat, description=desc, amount=amt, created_at=days_ago(d)))

        db.add(BusinessAlert(business_id=biz_a.id, alert_type="inventory", severity="warning",
                             title="Potash (MOP) stock below minimum",
                             message="Only 18 bags in stock (minimum: 25). Kharif season demand expected to rise.",
                             action_type="reorder_stock"))
        db.add(BusinessAlert(business_id=biz_a.id, alert_type="market", severity="info",
                             title="Wheat procurement prices up +3.4% in regional APMC",
                             message="Current APMC spot price ₹2,680/Quintal — favorable for your farmer customers.",
                             action_type="view_mandi"))

        # ════════════════════════════════════════════════════════════════════
        # BUSINESS 3: Retail
        # ════════════════════════════════════════════════════════════════════
        biz_r = Business(
            owner_id=user.id, name="Sharma General Stores & Wholesale",
            category="Retail", gstin="21AABCS1429B3ZD",
            phone="+91 98765 43212", address="Shop No. 12, Gandhi Nagar Market",
            city="Rourkela", state="Odisha", pincode="769001",
            health_score=91,
        )
        db.add(biz_r); db.flush()

        sup_r1 = Supplier(business_id=biz_r.id, name="Hindustan Unilever Distributor", phone="9437300001",
                          category="FMCG", city="Bhubaneswar", total_purchased=620000, pending_payable=55000, rating=4.9)
        sup_r2 = Supplier(business_id=biz_r.id, name="ITC Agarbatti & Confectionery", phone="9437300002",
                          category="FMCG", city="Rourkela", total_purchased=185000, pending_payable=22000, rating=4.6)
        db.add_all([sup_r1, sup_r2]); db.flush()

        prods_r = [
            Product(business_id=biz_r.id, name="Rice (Sona Masuri 25kg bag)", category="Staples",
                    unit="bag", purchase_price=1150, selling_price=1320, mrp=1400,
                    stock_quantity=85, min_stock_level=20, gst_rate=0, hsn_code="1006",
                    supplier_id=sup_r1.id),
            Product(business_id=biz_r.id, name="Aashirvaad Atta (10kg)", category="Staples",
                    unit="packet", purchase_price=385, selling_price=420, mrp=440,
                    stock_quantity=48, min_stock_level=15, gst_rate=5, hsn_code="1101",
                    supplier_id=sup_r1.id),
            Product(business_id=biz_r.id, name="Fortune Sunflower Oil (5 Litre)", category="Edible Oil",
                    unit="tin", purchase_price=620, selling_price=685, mrp=720,
                    stock_quantity=32, min_stock_level=10, gst_rate=5, hsn_code="1512",
                    supplier_id=sup_r1.id),
            Product(business_id=biz_r.id, name="Tata Salt (1kg)", category="Staples",
                    unit="packet", purchase_price=18, selling_price=22, mrp=24,
                    stock_quantity=220, min_stock_level=50, gst_rate=0, hsn_code="2501",
                    supplier_id=sup_r1.id),
            Product(business_id=biz_r.id, name="Surf Excel (1kg)", category="Cleaning",
                    unit="packet", purchase_price=95, selling_price=115, mrp=125,
                    stock_quantity=65, min_stock_level=20, gst_rate=18, hsn_code="3402",
                    supplier_id=sup_r1.id),
            Product(business_id=biz_r.id, name="Maggi Noodles (12-pack box)", category="Packaged Food",
                    unit="box", purchase_price=132, selling_price=148, mrp=156,
                    stock_quantity=28, min_stock_level=10, gst_rate=12, hsn_code="1902",
                    supplier_id=sup_r2.id),
        ]
        db.add_all(prods_r); db.flush()

        custs_r = [
            Customer(business_id=biz_r.id, name="Anita Devi (Regular)", phone="9437400001",
                     city="Rourkela", total_purchased=15800, total_paid=15800, pending_amount=0),
            Customer(business_id=biz_r.id, name="Pintu Canteen (Bulk)", phone="9437400002",
                     city="Rourkela", total_purchased=68000, total_paid=60000, pending_amount=8000),
            Customer(business_id=biz_r.id, name="Deepak Hostel Mess", phone="9437400003",
                     city="Rourkela", total_purchased=92000, total_paid=88000, pending_amount=4000),
            Customer(business_id=biz_r.id, name="Lalita Store (Wholesale)", phone="9437400004",
                     city="Sundargarh", total_purchased=185000, total_paid=180000, pending_amount=5000),
        ]
        db.add_all(custs_r); db.flush()

        rice = prods_r[0]; atta = prods_r[1]; oil = prods_r[2]; salt = prods_r[3]
        for i, (qty, prod, cust, paid_frac, ch, d) in enumerate([
            (20, rice,  custs_r[3], 1.0, "app", 1),
            (30, atta,  custs_r[2], 1.0, "whatsapp", 2),
            (10, oil,   custs_r[1], 0.875, "app", 3),
            (50, salt,  custs_r[0], 1.0, "walk_in", 4),
            (25, rice,  custs_r[2], 1.0, "app", 6),
            (15, atta,  custs_r[3], 1.0, "whatsapp", 8),
            (20, oil,   custs_r[1], 0.85, "app", 10),
            (8,  rice,  custs_r[0], 1.0, "walk_in", 12),
            (40, salt,  custs_r[2], 1.0, "app", 14),
            (12, rice,  custs_r[3], 1.0, "app", 16),
            (18, atta,  custs_r[1], 1.0, "whatsapp", 18),
            (6,  oil,   custs_r[0], 1.0, "walk_in", 20),
        ]):
            sub = round(prod.selling_price * qty, 2)
            gst = round(sub * prod.gst_rate / 100, 2)
            total = round(sub + gst, 2)
            paid = round(total * paid_frac, 2)
            status = "paid" if paid >= total else "partially_paid" if paid > 0 else "pending"
            db.add(Order(
                business_id=biz_r.id, customer_id=cust.id, product_id=prod.id,
                quantity=qty, unit_price=prod.selling_price, mrp=prod.mrp or prod.selling_price,
                discount=0, taxable_amount=sub, cgst_amount=round(gst/2, 2),
                sgst_amount=round(gst - round(gst/2, 2), 2), gst_amount=gst,
                total_amount=total, cost_amount=round(prod.purchase_price * qty, 2),
                amount_paid=paid, status=status, channel=ch,
                invoice_no=f"INV-{datetime.now().strftime('%Y%m%d')}-R{i+1:03d}",
                created_at=days_ago(d),
            ))

        for cat, desc, amt, d in [
            ("Transport", "Auto delivery to wholesale customers", 2200, 3),
            ("Electricity", "Shop electricity bill — October",    1800, 8),
            ("Labour",    "Part-time shop assistant — 2 weeks",   5600, 12),
            ("Rent",      "Shop rent — October",                  9000, 15),
            ("Packaging", "Paper bags and packaging material",    1200, 18),
        ]:
            db.add(Expense(business_id=biz_r.id, category=cat, description=desc, amount=amt, created_at=days_ago(d)))

        db.add(BusinessAlert(business_id=biz_r.id, alert_type="payment", severity="warning",
                             title="₹8,000 pending from Pintu Canteen",
                             message="Outstanding ₹8,000 since 10 days. Send payment reminder.",
                             action_type="whatsapp_reminder"))

        # WhatsApp demo chats
        db.add(WhatsAppChat(
            business_id=biz_c.id, customer_phone="9876511111",
            customer_name="Rahul Verma", status="quoted",
            message_in="Need 50 bags of 43 grade cement",
            ai_detected_product="OPC 53 Grade Cement", ai_quantity=50,
            ai_reply="Namaste Rahul ji! 🙏\n\nHere's your quotation from Sharma Construction:\n\n📦 OPC 53 Grade Cement\n🔢 Quantity: 50 bag\n💵 Rate: ₹375.00/bag\n📊 GST (28%): ₹5,250.00\n💰 Total: ₹24,000.00\n\nReply BUY to confirm.",
            created_at=days_ago(1),
        ))

        db.commit()
        print("✅ Demo data seeded successfully!")
        print("   📧 Email: demo@businessmanager.local")
        print("   🔑 Password: DemoPass123!")
        print("   🏢 3 businesses: Construction, Agriculture, Retail")

    except Exception as e:
        db.rollback()
        print(f"❌ Seeding failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
