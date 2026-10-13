"""
Business Manager — Economic Intelligence Service
Curated Indian market data: commodities, macro indicators, schemes, tenders.
AI market-impact analysis via Gemini.

DISCLAIMER: All prices are indicative benchmark values for educational/business planning
purposes. Verify current prices from official sources before making purchasing decisions.
AI market analysis represents Gemini's interpretation, not professional financial advice.
"""
from __future__ import annotations
from .ai_service import call_gemini

# ── Static data feeds (refresh periodically in production) ──────────────────

COMMODITIES = [
    # Construction
    {"id": "c1",  "name": "TMT Steel 500D (12mm)",       "category": "Construction",  "price": "₹54,200/Ton",    "change": "+2.8%",  "trend": "up",      "impact": "Higher project rebar cost"},
    {"id": "c2",  "name": "OPC 53 Grade Cement",          "category": "Construction",  "price": "₹375/Bag",       "change": "-1.2%",  "trend": "down",    "impact": "Favorable buying window"},
    {"id": "c3",  "name": "River Sand (Coarse)",           "category": "Construction",  "price": "₹52/Cu.Ft",     "change": "+4.1%",  "trend": "up",      "impact": "Supply tightening"},
    {"id": "c4",  "name": "Fly Ash Bricks (1000 pcs)",    "category": "Construction",  "price": "₹5,800/1000",   "change": "+1.5%",  "trend": "up",      "impact": "Cost increase for masonry"},
    {"id": "c5",  "name": "Plywood 18mm (8×4 ft)",        "category": "Construction",  "price": "₹2,150/Sheet",  "change": "0.0%",   "trend": "neutral", "impact": "Stable shuttering cost"},
    # Agriculture
    {"id": "a1",  "name": "Wheat (Sharbati) APMC Spot",   "category": "Agriculture",   "price": "₹2,680/Quintal","change": "+3.4%",  "trend": "up",      "impact": "High procurement demand"},
    {"id": "a2",  "name": "Paddy (Common Grade)",          "category": "Agriculture",   "price": "₹2,183/Quintal","change": "+0.8%",  "trend": "up",      "impact": "MSP procurement active"},
    {"id": "a3",  "name": "Mustard Seed Mandi Spot",       "category": "Agriculture",   "price": "₹5,420/Quintal","change": "+1.8%",  "trend": "up",      "impact": "Crusher mill demand active"},
    {"id": "a4",  "name": "DAP Fertilizer (50kg bag)",     "category": "Agriculture",   "price": "₹1,350/Bag",    "change": "0.0%",   "trend": "neutral", "impact": "Government subsidy stable"},
    {"id": "a5",  "name": "Urea (45kg bag)",               "category": "Agriculture",   "price": "₹266/Bag",      "change": "0.0%",   "trend": "neutral", "impact": "Fixed under Neem coating policy"},
    # Retail / General
    {"id": "r1",  "name": "Commercial Diesel (Avg)",       "category": "All",           "price": "₹89.62/Litre",  "change": "+0.5%",  "trend": "up",      "impact": "Transport expense increased ~1%"},
    {"id": "r2",  "name": "PVC Pipe (4-inch, per foot)",   "category": "Construction",  "price": "₹68/ft",        "change": "+2.1%",  "trend": "up",      "impact": "Plumbing cost increase"},
    {"id": "r3",  "name": "Edible Oil (Soybean, 15 kg)",   "category": "Retail",        "price": "₹1,320/Tin",    "change": "-3.2%",  "trend": "down",    "impact": "FMCG margin may improve"},
]

MACRO_INDICATORS = [
    {"name": "RBI Repo Rate",             "value": "6.50%", "status": "Neutral",             "implication": "Working capital loan cost stable"},
    {"name": "CPI Retail Inflation",      "value": "4.85%", "status": "Within RBI target",    "implication": "Consumer demand resilient"},
    {"name": "GST Collections (Monthly)", "value": "₹1.87 Lakh Cr", "status": "Robust growth","implication": "E-way bill compliance enforcement active"},
    {"name": "WPI Inflation",             "value": "2.18%", "status": "Softening",            "implication": "Wholesale input costs easing slightly"},
    {"name": "Infrastructure Spending",   "value": "₹11.1 Lakh Cr (FY25 Budget)", "status": "Peak season", "implication": "Strong government order pipeline for contractors"},
]

GOVERNMENT_SCHEMES = [
    {
        "id": "s1",
        "name": "PM Vishwakarma Scheme",
        "target": "Traditional artisans, masons, carpenters, blacksmiths",
        "benefit": "Collateral-free loan up to ₹3 Lakh at 5% interest + ₹15,000 toolkit grant + skill training",
        "eligible_categories": ["Construction", "Retail", "Other"],
        "portal": "pmvishwakarma.gov.in",
        "deadline": "Ongoing",
        "ai_tip": "Ideal for skilled trade workers and small workshop owners.",
    },
    {
        "id": "s2",
        "name": "PMEGP (PM Employment Generation Programme)",
        "target": "Manufacturing and service MSMEs",
        "benefit": "15–35% government subsidy on project loans up to ₹50 Lakh (manufacturing) / ₹20 Lakh (service)",
        "eligible_categories": ["Retail", "Agriculture", "Construction", "Other"],
        "portal": "kviconline.gov.in",
        "deadline": "Ongoing",
        "ai_tip": "High subsidy for first-generation entrepreneurs in rural and semi-urban areas.",
    },
    {
        "id": "s3",
        "name": "PM Kisan Samman Nidhi",
        "target": "Small and marginal farmers (< 2 hectares)",
        "benefit": "₹6,000/year direct income support in 3 installments of ₹2,000",
        "eligible_categories": ["Agriculture"],
        "portal": "pmkisan.gov.in",
        "deadline": "Ongoing",
        "ai_tip": "Automatic transfer to registered bank accounts. Register at CSC or nearest bank.",
    },
    {
        "id": "s4",
        "name": "GeM Portal — MSME Procurement Preference",
        "target": "Registered MSME contractors and suppliers",
        "benefit": "Government procurement preference, tender fee exemption, faster payments",
        "eligible_categories": ["Retail", "Construction", "Agriculture", "Other"],
        "portal": "gem.gov.in",
        "deadline": "Always open",
        "ai_tip": "Sell directly to government departments. Strong push from ₹3 Lakh Cr annual procurement target.",
    },
    {
        "id": "s5",
        "name": "NABARD Kisan Credit Card",
        "target": "Farmers and agriculture-allied businesses",
        "benefit": "Revolving credit up to ₹3 Lakh at 4% interest (with ₹1.5 Lakh limit at 2% after interest subvention)",
        "eligible_categories": ["Agriculture"],
        "portal": "nabard.org",
        "deadline": "Ongoing",
        "ai_tip": "Low-cost working capital for seasonal agri-input purchases.",
    },
    {
        "id": "s6",
        "name": "Credit Guarantee Fund Trust for Micro & Small (CGTMSE)",
        "target": "Micro and small enterprises",
        "benefit": "Collateral-free loans up to ₹2 Crore guaranteed by government to lending banks",
        "eligible_categories": ["Retail", "Construction", "Agriculture", "Other"],
        "portal": "cgtmse.in",
        "deadline": "Ongoing",
        "ai_tip": "Apply through your bank. No collateral needed — government is your guarantor.",
    },
]

TENDERS = [
    {
        "id": "t1",
        "tender_ref": "RWD/PMGSY/ODI/2026/001",
        "title": "Construction of Rural Concrete Roads & Culverts under PMGSY Phase-IV",
        "department": "Rural Works Department, Government of Odisha",
        "location": "Mayurbhanj / Balasore, Odisha",
        "state": "Odisha",
        "value_lakhs": 48.5,
        "deadline": "24 Oct 2026",
        "eligibility": "Class 'C' & 'B' licensed civil contractors with ₹25L+ annual turnover",
        "documents": "Valid GSTIN, PAN, Contractor License, 2-year ITR, EMD Bank Guarantee (2%)",
        "ai_summary": "Rural pavement and culvert work under flagship PMGSY program. 3-year defect liability. High fit for small-to-mid construction contractors.",
        "source_url": "https://tendersodisha.gov.in",
        "category_fit": ["Construction"],
    },
    {
        "id": "t2",
        "tender_ref": "AGRI/PMKSY/ODI/2026/015",
        "title": "Supply and Installation of Drip Irrigation & Sprinkler Systems (Per Drop More Crop)",
        "department": "Dept. of Agriculture and Farmers' Welfare, Odisha",
        "location": "Cuttack / Khordha, Odisha",
        "state": "Odisha",
        "value_lakhs": 22.0,
        "deadline": "28 Oct 2026",
        "eligibility": "Authorized dealers/suppliers of BIS-certified micro-irrigation equipment",
        "documents": "BIS Certificate, Manufacturer Authorization, GST Registration, 1-year experience",
        "ai_summary": "Micro-irrigation supply under PMKSY. Ideal for agri-equipment dealers and distributors. Significant volume for established suppliers.",
        "source_url": "https://agri.odisha.gov.in",
        "category_fit": ["Agriculture"],
    },
    {
        "id": "t3",
        "tender_ref": "SWC/GDN/2026/087",
        "title": "Construction of Modern Grain Storage Godown (500 MT Capacity) with RCC Structure",
        "department": "Odisha State Warehousing Corporation",
        "location": "Sambalpur, Odisha",
        "state": "Odisha",
        "value_lakhs": 85.0,
        "deadline": "05 Nov 2026",
        "eligibility": "Class 'A' & 'B' civil and structural contractors with similar warehouse completion certificate",
        "documents": "Solvency Certificate, Technical Bid with structural design, Completion certificates",
        "ai_summary": "Large structural civil and steel project. Requires strong structural capability. Excellent for experienced construction contractors.",
        "source_url": "https://eprocure.gov.in",
        "category_fit": ["Construction"],
    },
    {
        "id": "t4",
        "tender_ref": "ORE/SOLAR/2026/044",
        "title": "Supply of Solar Pumps for Agricultural Irrigation (PM KUSUM Component-B)",
        "department": "Odisha Renewable Energy Development Agency (OREDA)",
        "location": "Multiple Districts, Odisha",
        "state": "Odisha",
        "value_lakhs": 35.0,
        "deadline": "15 Nov 2026",
        "eligibility": "Empanelled solar pump suppliers / MNRE-approved system integrators",
        "documents": "MNRE empanelment certificate, GST, 3-year audited financials",
        "ai_summary": "Government solar pump supply under PM KUSUM scheme. Good fit for agri-equipment and renewable energy dealers.",
        "source_url": "https://oreda.gov.in",
        "category_fit": ["Agriculture", "Construction"],
    },
    {
        "id": "t5",
        "tender_ref": "SMC/BLD/2026/112",
        "title": "Renovation and Painting Works of Municipal Buildings & Schools",
        "department": "Sambalpur Municipal Corporation",
        "location": "Sambalpur, Odisha",
        "state": "Odisha",
        "value_lakhs": 12.5,
        "deadline": "18 Nov 2026",
        "eligibility": "Class 'C' & 'D' licensed civil contractors registered with PWD/ULB",
        "documents": "Contractor registration certificate, GST, PAN, EMD",
        "ai_summary": "Small-to-medium municipal renovation contract. Low competition, quick payment cycle from municipal fund. Ideal for small contractors.",
        "source_url": "https://sambalpur.nic.in/tenders",
        "category_fit": ["Construction"],
    },
]


# ── Public API ───────────────────────────────────────────────────────────────

def get_economic_intelligence(category: str = "All") -> dict:
    """Returns market data filtered by business category."""
    if category == "All":
        commodities = COMMODITIES
    else:
        commodities = [c for c in COMMODITIES if c["category"] in (category, "All")]

    tenders = [t for t in TENDERS if category == "All" or category in t.get("category_fit", [])]
    schemes = [s for s in GOVERNMENT_SCHEMES if category == "All" or category in s.get("eligible_categories", [])]

    return {
        "commodities": commodities,
        "macro_indicators": MACRO_INDICATORS,
        "schemes": schemes,
        "tenders": tenders,
        "disclaimer": (
            "Prices are indicative benchmark values for planning purposes only. "
            "AI market analysis is Gemini's interpretation — not professional financial advice. "
            "Verify current rates from official sources before purchasing decisions."
        ),
    }


def get_market_impact_analysis(category: str, business_name: str) -> str:
    """AI explanation of how current market conditions affect this specific business."""
    prompt = (
        f"Business: '{business_name}' | Category: {category}\n\n"
        f"Current Indian market snapshot (October 2026):\n"
        f"• TMT Steel up +2.8% (₹54,200/Ton)\n"
        f"• Cement eased -1.2% (₹375/Bag)\n"
        f"• River Sand up +4.1% — supply tightening\n"
        f"• Wheat up +3.4% — high procurement demand\n"
        f"• Commercial Diesel +0.5% — transport cost uptick\n"
        f"• RBI Repo Rate stable at 6.50%\n"
        f"• Govt infra spending at peak seasonal pace\n\n"
        f"Write 3 concise bullet points:\n"
        f"• What does this mean specifically for my {category} business?\n"
        f"• One immediate cost-saving action I can take.\n"
        f"• One revenue opportunity I should explore.\n\n"
        f"Use ₹ formatting. Be practical and specific."
    )
    return call_gemini(
        prompt,
        f"You are a practical economic advisor for Indian {category} business owners.",
        max_tokens=400,
    )


def get_tender_ai_summary(tender_id: str, business_category: str) -> str:
    """Deep-dive AI analysis on a specific tender's fit for the business."""
    tender = next((t for t in TENDERS if t["id"] == tender_id), None)
    if not tender:
        return "Tender not found."

    prompt = (
        f"Tender: {tender['title']}\n"
        f"Department: {tender['department']}\n"
        f"Location: {tender['location']}\n"
        f"Value: ₹{tender['value_lakhs']} Lakhs\n"
        f"Deadline: {tender['deadline']}\n"
        f"Eligibility: {tender['eligibility']}\n"
        f"Documents: {tender['documents']}\n\n"
        f"My business category: {business_category}\n\n"
        f"Analyse this tender and answer:\n"
        f"1. How suitable is this for my business? (High/Medium/Low fit)\n"
        f"2. Key requirements I must meet.\n"
        f"3. Estimated preparation time and key risks.\n"
        f"4. One specific advantage I might have.\n\n"
        f"Be concise and actionable."
    )
    return call_gemini(
        prompt,
        "You are a government tender advisor for Indian MSME contractors.",
        max_tokens=500,
    )
