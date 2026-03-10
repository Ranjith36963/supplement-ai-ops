# Supplement AI Operations Suite

AI-powered voice booking & customer support automation for health supplement businesses.

**One unified system:** Customer calls via Retell AI voice agent → n8n orchestrates → FastAPI + OpenAI processes → booking confirmed or support query handled.

---

## Live Demo

**[Try it live →](https://ranjith36963.github.io/supplement-ai-ops/)**

---

## Architecture Overview

```
Customer Voice Call (Retell AI)
        │
        ▼
n8n Webhook (supplement-reception)
        │
        ▼
AI Classify Request → FastAPI on Railway → OpenAI GPT-4o-mini
        │
        ├── BOOKING → Extract date, time, health concerns
        │             → Suggest supplement → Confirm booking
        │
        └── SUPPORT → Classify category (shipping, billing, product, etc.)
                    → Assess priority & sentiment
                    → Generate auto-response → Route to team if needed

Error handling: Retry logic (3x) • Fallback responses • Structured logging
```

## How It Works

| Input Method | What Happens |
|-------------|-------------|
| Voice call (Retell AI) | Customer speaks naturally → AI receptionist collects name, health concerns, preferred time → triggers n8n webhook → books consultation |
| Text (Booking) | Customer sends booking request → AI extracts intent, date, time, health concerns → suggests supplement → confirms booking |
| Text (Support) | Customer sends support query → AI classifies by category, priority, sentiment → generates auto-response → routes if needed |

All three inputs hit the **same n8n webhook** — the AI backend decides whether it's a booking or support request and routes accordingly.

---

## Tech Stack

- **Voice AI:** Retell AI (conversation flow agent, browser-based calls)
- **Orchestration:** n8n (single webhook, smart routing via IF node)
- **AI Backend:** FastAPI + Python (intent extraction, triage, suggestions)
- **AI Model:** OpenAI GPT-4o-mini (cost-effective, fast)
- **Hosting:** Railway (backend API, auto-deploy from GitHub)
- **Error Handling:** Retries (3x), fallback responses, structured logging

---

## n8n Workflow: Supplement AI Reception

One workflow handles everything:

```
Reception Webhook → AI Classify Request → Booking or Support?
                                              │
                                    ┌─── YES (Booking) ───┐
                                    │                      │
                              Process Booking    Respond - Booking Confirmed
                                    │
                                    └─── NO (Support) ────┐
                                                           │
                              AI Support Triage → Process Support Query → Respond - Support Handled
```

**Nodes:**
- **Reception Webhook** — Single POST endpoint receiving all requests
- **AI Classify Request** — Sends to FastAPI backend, OpenAI determines intent
- **Booking or Support?** — IF node routes based on intent
- **Process Booking** — Extracts date, time, health concerns, supplement suggestion
- **AI Support Triage** — Classifies category, priority, sentiment, generates response
- **Respond** — Returns structured JSON to caller

---

## Retell AI Voice Agent

**Agent:** Supplement Consultation Booking

**Conversation Flow:**
1. **Welcome** → Greets customer, asks for name
2. **Health Concerns** → Asks what they need help with (focus, energy, mood, immune)
3. **Preferred Time** → Asks when they'd like their consultation
4. **Confirm Booking** → Triggers n8n webhook via custom function, confirms appointment

**Custom Function:** `book_consultation` — POST to n8n webhook with customer name, health concerns, and preferred time.

---

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/booking/process` | POST | Process booking requests via AI |
| `/api/support/triage` | POST | Triage and classify support queries |
| `/api/retell/create-web-call` | POST | Create browser-based Retell voice call |
| `/health` | GET | Health check |

---

## Testing

**Test Booking:**
```bash
curl -X POST https://ranjith36963.app.n8n.cloud/webhook/supplement-reception \
  -H "Content-Type: application/json" \
  -d '{"message": "I need help with focus and energy. Can I book for Thursday at 2pm?", "customer_name": "Sarah Johnson", "customer_email": "sarah@example.com"}'
```

**Test Support:**
```bash
curl -X POST https://ranjith36963.app.n8n.cloud/webhook/supplement-reception \
  -H "Content-Type: application/json" \
  -d '{"message": "I ordered the focus supplement last week but havent received it. Order ORD-12345.", "customer_name": "James Wilson", "order_id": "ORD-12345"}'
```

---

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| Single webhook for all requests | Simpler architecture, AI handles routing |
| Retell AI for voice | Browser-based testing, no phone costs for demo |
| Separate FastAPI backend | Keeps AI logic testable, versionable, reusable |
| GPT-4o-mini | Cost-effective for production, fast enough for real-time |
| Retry logic on HTTP nodes | Production systems must handle transient failures |
| Fallback responses | Users always get a response, even if AI fails |

---

## File Structure

```
supplement-ai-ops/
├── index.html              # Live demo page (GitHub Pages)
├── backend/
│   ├── main.py             # FastAPI app (booking, support, Retell endpoints)
│   ├── requirements.txt    # Python dependencies
│   ├── Procfile            # Railway start command
│   └── railway.json        # Railway config
└── README.md               # This file
```

---

Built by [Ranjith Maliga Guruprakash](https://ranjith36963.github.io) — AI/ML Engineer