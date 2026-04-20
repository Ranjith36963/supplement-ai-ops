# Supplement AI Operations Suite

AI-powered voice booking & customer support automation for health supplement businesses.

**One unified system:** Customer calls via Retell AI voice agent → n8n orchestrates → FastAPI + OpenAI processes → Google Calendar books event + Slack notifies team.

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
        │             → Suggest supplement
        │             → Google Calendar: Create Event (via REST API)
        │             → Slack #bookings: Notification
        │             → Confirm booking
        │
        └── SUPPORT → Classify category (shipping, billing, product, etc.)
                    → Assess priority & sentiment
                    → Generate auto-response
                    → Slack #support: Notification
                    → Route to team if needed
```

## How It Works

| Input Method | What Happens |
|-------------|-------------|
| Voice call (Retell AI) | Customer speaks naturally → AI receptionist collects name, health concerns, preferred time → triggers n8n webhook → books consultation → creates Google Calendar event → notifies Slack |
| Text (Booking) | Customer sends booking request → AI extracts intent, date, time, health concerns → suggests supplement → creates calendar event → Slack notification → confirms booking |
| Text (Support) | Customer sends support query → AI classifies by category, priority, sentiment → generates auto-response → Slack notification → routes if needed |

All inputs hit the **same n8n webhook** — the AI backend decides whether it's a booking or support request and routes accordingly. The webhook handles both Retell custom function payloads (`body.args`) and direct POST payloads (`body.message`).

---

## Tech Stack

- **Voice AI:** Retell AI (conversation flow agent, browser-based calls)
- **Orchestration:** n8n (single workflow, smart routing via IF node)
- **AI Backend:** FastAPI + Python (intent extraction, triage, suggestions)
- **AI Model:** OpenAI GPT-4o-mini (cost-effective, fast)
- **Calendar:** Google Calendar REST API via OAuth2 (automatic event creation on booking)
- **Notifications:** Slack (`#bookings` and `#support` channel notifications via webhooks)
- **Hosting:** Railway (backend API, auto-deploy from GitHub)
- **Demo:** GitHub Pages (static demo page)

---

## n8n Workflow: Supplement AI Reception — Booking & Support

One workflow handles everything:

```
Reception Webhook → AI Classify Request → Booking or Support?
                                              │
                                    ┌─── YES (Booking) ──────────────────────┐
                                    │                                         │
                              Process Booking                                 │
                                    │                                         │
                                    ├── Google Calendar Create Event (REST)    │
                                    ├── Slack Booking Notification             │
                                    │                                         │
                                    └── Respond - Booking Confirmed ──────────┘

                                    ┌─── NO (Support) ───────────────────────┐
                                    │                                         │
                              AI Support Triage                               │
                                    │                                         │
                                    ├── Slack Support Notification             │
                                    │                                         │
                                    └── Respond - Support Handled ────────────┘
```

**Nodes:**
- **Reception Webhook** — Single POST endpoint (`/webhook/supplement-reception`) receiving all requests
- **AI Classify Request** — Calls `/api/booking/process` on Railway backend; handles both Retell (`body.args`) and direct webhook (`body`) payloads
- **Booking or Support?** — IF node routes based on intent (`book_consultation` → booking path, everything else → support path)
- **Process Booking** — Extracts structured booking data from AI response (customer name, date, time, health concerns, supplement suggestion)
- **Google Calendar Create Event** — HTTP Request to Google Calendar REST API with OAuth2 credentials; creates 1-hour event with customer name, health concerns, and supplement in description; timezone set to Europe/London
- **Slack Booking Notification** — Posts to `#bookings` channel with full booking details
- **Respond - Booking Confirmed** — Returns confirmation JSON to caller
- **AI Support Triage** — Calls `/api/support/triage` on Railway backend for classification
- **Slack Support Notification** — Posts to `#support` channel with category, priority, sentiment, and auto-response
- **Respond - Support Handled** — Returns triage JSON to caller

---

## Retell AI Voice Agent

**Agent:** Supplement Consultation Booking
**Agent ID:** `agent_37a7d4939e00d23cd9a4dd1e8b`
**Preview:** [Try voice agent →](https://agent.retellai.com/preview/agent_37a7d4939e00d23cd9a4dd1e8b)
**Voice:** Cimo | **Language:** English | **Execution Mode:** Rigid Mode

**Conversation Flow (4 nodes):**
1. **Welcome Node** → Greets customer, asks for name
2. **Health Concerns** → Asks what they need help with (focus, energy, mood, immune)
3. **Preferred Time** → Asks when they'd like their consultation
4. **Confirm Booking** → Triggers n8n webhook via `book_consultation` custom function, confirms appointment

**Custom Function:** `book_consultation` — POST to n8n webhook (`https://ranjith369.app.n8n.cloud/webhook/supplement-reception`) with `message`, `customer_name`, and `customer_email` fields.

**Post-Call Webhook:** Retell sends call transcripts to Railway (`/api/retell/webhook`), which forwards them to n8n for processing. This provides a second path for voice data to reach the workflow.

---

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/booking/process` | POST | Process booking requests via AI — extracts intent, date, time, health concerns, suggests supplements |
| `/api/support/triage` | POST | Triage and classify support queries — category, priority, sentiment, auto-response |
| `/api/retell/create-web-call` | POST | Create browser-based Retell voice call (returns access token) |
| `/api/retell/webhook` | POST | Receive Retell post-call events, forward transcript to n8n |
| `/health` | GET | Health check |

---

## Integrations

| Service | Purpose | Channel/Details |
|---------|---------|-----------------|
| Google Calendar | Automatic event creation | Creates 1-hour consultation events on confirmed bookings via REST API with OAuth2 |
| Slack | Team notifications | `#bookings` for new bookings, `#support` for support queries |
| Retell AI | Voice agent | Browser-based calls via Web SDK; custom function triggers n8n webhook on booking |
| OpenAI | AI processing | GPT-4o-mini for intent extraction, date/time parsing, supplement suggestion, and support triage |

---

## Testing

**Test via n8n webhook (full pipeline — booking):**

```bash
curl -X POST https://ranjith369.app.n8n.cloud/webhook/supplement-reception \
  -H "Content-Type: application/json" \
  -d '{"message": "I need help with focus and energy. Can I book for Thursday at 2pm?", "customer_name": "Sarah Johnson", "customer_email": "sarah@example.com"}'
```

**Test via n8n webhook (full pipeline — support):**

```bash
curl -X POST https://ranjith369.app.n8n.cloud/webhook/supplement-reception \
  -H "Content-Type: application/json" \
  -d '{"message": "I ordered the focus supplement last week but havent received it. Order ORD-12345.", "customer_name": "James Wilson", "order_id": "ORD-12345"}'
```

**Test backend directly (booking):**

```bash
curl -X POST https://supplement-ai-ops-production.up.railway.app/api/booking/process \
  -H "Content-Type: application/json" \
  -d '{"message": "I need help with focus and energy. Can I book for Thursday at 2pm?", "customer_name": "Sarah Johnson", "customer_email": "sarah@example.com"}'
```

**Test backend directly (support):**

```bash
curl -X POST https://supplement-ai-ops-production.up.railway.app/api/support/triage \
  -H "Content-Type: application/json" \
  -d '{"message": "I ordered the focus supplement last week but havent received it. Order ORD-12345.", "customer_name": "James Wilson", "order_id": "ORD-12345"}'
```

---

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| Single webhook for all requests | Simpler architecture, AI handles routing |
| Google Calendar via REST API | n8n's native Calendar node (v1.3) has a confirmed bug with dynamic expressions on Cloud v2.10.3; HTTP Request + OAuth2 bypasses it reliably |
| Retell AI for voice | Browser-based testing, no phone costs for demo |
| Separate FastAPI backend | Keeps AI logic testable, versionable, reusable |
| GPT-4o-mini | Cost-effective for production, fast enough for real-time |
| Slack webhook notifications | Team gets instant alerts, separate channels for booking vs support |
| Dual payload handling (`body.args` / `body.message`) | Retell custom functions send data in `args`, while direct webhooks and Railway forwarding send in `body` — the workflow handles both |
| Retry logic on HTTP nodes | Production systems must handle transient failures |
| Fallback responses | Users always get a response, even if AI fails |

---

## Setup & Redeploy

1. Clone repo
2. Copy `.env.example` to `.env` and fill in values
3. Deploy `main.py` to Railway, set env vars in Railway dashboard
4. Import `n8n-workflow.json` into n8n
5. In n8n, set real Slack webhook URLs in the two Slack notification nodes
6. In n8n, connect Google Calendar via OAuth2 credential
7. Update `N8N_WEBHOOK_URL` and `BACKEND_URL` in `index.html` to your URLs
8. Push `index.html` to GitHub Pages

---

## File Structure

```
supplement-ai-ops/
├── index.html          # Live demo page (GitHub Pages)
├── main.py             # FastAPI app (booking, support, Retell endpoints)
├── n8n-workflow.json    # n8n workflow definition (import into n8n)
├── requirements.txt    # Python dependencies
├── Procfile            # Railway start command
├── railway.json        # Railway config
├── .nojekyll           # Bypass Jekyll processing on GitHub Pages
└── README.md           # This file
```

---

Built by [Ranjith Maliga Guruprakash](https://ranjith36963.github.io) — AI/ML Engineer
