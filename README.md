# Business Manager — AI Business Operating System (India)

A real, production-ready AI-powered Business Operating System built specifically for Indian MSME business owners (Shopkeepers/Retail, Construction & Infra Contractors, Agriculture & Krishi Kendras).

Combines:
- 🤖 **Google Gemini 2.5 Flash AI Assistant**: Real-time database grounding with function querying.
- 🎤 **Voice Commands**: Speaks & understands Hindi, Hinglish, Odia, and English.
- 💬 **WhatsApp Business Automation**: Auto product detection, stock checking, 18% GST auto-calculation, and 1-tap `[ BUY ]` order creation.
- 📊 **Business Health Score (0–100)**: With Gemini AI diagnostic reasoning explaining why the score moved.
- ✦ **"What Should I Do Today?" Action Plan**: Priority cash collection reminders, stock reorders, and market opportunities.
- 🏗️ **Multi-Business Switcher**: Seamlessly toggle between Construction, Agriculture, and Retail businesses.
- 🧾 **GST Tax Invoices**: Full GSTIN, CGST/SGST tax breakdown, HSN codes, and 1-tap WhatsApp sharing.
- 📈 **Economic & Tender Intelligence**: Mandi commodity rates, APMC spot prices, MSME schemes, and official public tenders.

---

## 1. Zero-Cost Technology Stack & Architecture

| Feature | Provider / Tool | Zero-Cost Tier / Details |
| :--- | :--- | :--- |
| **AI Engine** | **Google Gemini 2.5 Flash** | Free tier via Google AI Studio (Active & tested). |
| **Voice Commands** | Android Native SpeechRecognizer | 100% free on-device Google Voice Input (Hindi, Odia, English). |
| **WhatsApp Integration** | Meta WhatsApp Cloud API | 1,000 free service conversations per month. |
| **Database** | SQLite (Local) / Supabase (Cloud) | Free tier 500MB PostgreSQL on Supabase or local SQLite. |
| **Backend API** | FastAPI + Python 3.11 | High performance, async REST APIs. |
| **Mobile App** | React Native + Expo | Cross-platform Android-first client. |

---

## 2. Quick Start & Running Locally

### Step A: Backend is Running
The FastAPI backend is currently active on port `8000`:
- **API Health Check**: http://127.0.0.1:8000/health
- **Interactive Swagger Docs**: http://127.0.0.1:8000/docs

To run or restart manually at any time:
```powershell
cd backend
py -3.11 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Step B: Launch the Mobile App
In another PowerShell terminal:
```powershell
cd mobile
npx expo start
```
- **On a Physical Android Phone**: Install **Expo Go** from Google Play Store, ensure your phone is connected to the same Wi-Fi, and scan the QR code.
- **On Android Emulator**: Press `a` in the terminal to launch on the emulator.
- **On Web Browser**: Press `w` in the terminal to view in Chrome / Firefox.

---

## 3. Demo Account & Data Preloaded

- **Email**: `demo@businessmanager.local`
- **Password**: `DemoPass123!`

### Preloaded Indian Businesses:
1. 🏗️ **Sharma Building Materials & Infra** (Construction):
   - UltraTech Cement 43 Grade, Tata Tiscon TMT Steel 12mm, River Sand, Kiln Bricks.
   - Real customers (Rahul Verma, Patel Developers, Pooja Housing Works).
   - Real infrastructure projects (Royal Palms Complex, PWD Biju Setu Bridge Approach Road).
2. 🌾 **Kisan Agro Krishi Kendra** (Agriculture):
   - DAP Fertilizers, Certified Hybrid Wheat Seeds, Chlorpyrifos Pesticide.
3. 🏪 **Sharma Super Mart & Kirana** (Retail):
   - India Gate Basmati Rice, Fortune Kachi Ghani Mustard Oil.

---

## 4. Key Endpoints Implemented

- `POST /auth/login` & `POST /auth/register`: JWT authentication.
- `GET /businesses/{id}/dashboard`: Real-time financial calculations (sales, expenses, profit, receivables).
- `GET /businesses/{id}/ai/query?q=...`: Gemini 2.5 Flash grounded assistant.
- `GET /businesses/{id}/ai/health-score`: Computes 0-100 score + Gemini diagnostic analysis.
- `GET /businesses/{id}/ai/action-plan`: "What should I do today?" prioritized cards.
- `POST /businesses/{id}/whatsapp/simulate`: Simulated WhatsApp chat with AI product recognition & order creation.
- `POST /businesses/{id}/whatsapp/reminder`: Courteous payment reminder generation.
- `GET /businesses/{id}/orders/{order_id}/invoice`: Complete GST Tax Invoice details.
- `GET /businesses/{id}/economic`: Live commodity spot rates, MSME schemes & tenders.
