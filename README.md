# Supplement AI Operations Suite

AI-powered automation system for health supplement businesses — handling consultation booking, customer support triage, and content generation.

Built with **n8n** (orchestration) + **FastAPI** (AI backend) + **OpenAI** (intelligence).

---

## Architecture Overview

```
Customer Input → n8n Webhook → AI Backend (FastAPI/Railway) → OpenAI Processing → Action (Calendar/Email/Content)
                     ↓                                              ↓
              Error Handling                                   Retry Logic
              Logging                                          Fallback Responses
```

### Three Workflows

| Workflow | Purpose | n8n Nodes | AI Endpoint |
|----------|---------|-----------|-------------|
| WF1 - Smart Booking | Process consultation requests | Webhook → HTTP → Calendar → IF → Email | `/api/booking/process` |
| WF2 - Support Triage | Classify & route customer queries | Webhook → HTTP → Switch → Email/Escalate | `/api/support/triage` |
| WF3 - Content Pipeline | Generate marketing content variants | Webhook → HTTP → IF → Set → Email | `/api/content/generate` |

---

## Setup Guide

### Step 1: Deploy Backend to Railway

1. Create a new project on [railway.app](https://railway.app)
2. Connect your GitHub repo (or deploy from the `/backend` folder)
3. Add environment variable: `OPENAI_API_KEY=your_key_here`
4. Railway auto-detects Python and deploys
5. Note your public URL: `https://your-app.railway.app`
6. Test: Visit `https://your-app.railway.app/` — should show API info
7. Test health: `https://your-app.railway.app/health`

### Step 2: Import n8n Workflows

1. Open your n8n instance
2. Go to **Settings → Environment Variables** and add:
   - `API_BASE_URL` = `https://your-app.railway.app`
3. For each workflow JSON file:
   - Click **+** (new workflow)
   - Click **...** menu → **Import from File**
   - Select the workflow JSON
   - Activate the workflow

### Step 3: Connect Google Calendar

1. In n8n, go to **Settings → Credentials**
2. Add **Google Calendar OAuth2** credential
3. Authorise with your Google account
4. Update the Calendar nodes in WF1 to use your credential

### Step 4: Configure Email (Optional for Demo)

For the demo, email nodes can be left unconfigured — the workflow will still execute and show the flow. To make emails work:
1. Add SMTP credentials in n8n (Gmail, SendGrid, etc.)
2. Update email nodes with your credential

---

## Testing the Workflows

### Test WF1 - Smart Booking

```bash
curl -X POST https://your-n8n-url/webhook/booking-request \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hi, I have been struggling with focus and low energy lately. Can I book a consultation for next Thursday at 2pm?",
    "customer_name": "Sarah Johnson",
    "customer_email": "sarah@example.com"
  }'
```

**Expected:** AI extracts intent (book_consultation), date, time, health concerns (focus, energy), and suggests a supplement.

### Test WF2 - Support Triage

```bash
curl -X POST https://your-n8n-url/webhook/support-ticket \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I ordered the focus supplement last week but haven't received it yet. My order number is ORD-12345. Can you check the status?",
    "customer_name": "James Wilson",
    "customer_email": "james@example.com",
    "order_id": "ORD-12345"
  }'
```

**Expected:** AI classifies as "shipping", priority "medium", routes appropriately, drafts empathetic response.

### Test WF3 - Content Pipeline

```bash
curl -X POST https://your-n8n-url/webhook/content-generate \
  -H "Content-Type: application/json" \
  -d '{
    "brief": "Launch campaign for a new natural focus supplement targeting professionals aged 25-45 who struggle with afternoon energy dips and need sustained mental clarity for demanding work",
    "product_category": "focus",
    "tone": "professional"
  }'
```

**Expected:** AI generates email copy, 4 social media variants, 3 product descriptions, SEO keywords.

---

## Demo Walkthrough Script

### Opening (30 seconds)
"This is a complete AI operations suite I built for a health supplement business. It has three connected workflows handling booking, customer support, and content generation — all orchestrated through n8n with an AI backend I built using FastAPI and deployed on Railway."

### WF1 Demo (2 minutes)
1. Show the workflow visually in n8n
2. Trigger a test booking request
3. Walk through each node: "The webhook catches the request, sends it to my AI backend which extracts the intent, date, time, and health concerns. It then checks Google Calendar, books the slot, and sends a personalised confirmation with a supplement recommendation."
4. Highlight: error handling, retry logic, fallback for enquiries

### WF2 Demo (2 minutes)
1. Show the workflow visually
2. Trigger a complaint and a product question
3. Walk through: "The AI classifies the query by category, priority, and sentiment. High-confidence product questions get auto-replied. Complaints escalate to management. Billing queries route to the billing team. Everything is logged and tagged for analytics."
4. Highlight: the Switch node routing, confidence-based auto-reply

### WF3 Demo (2 minutes)
1. Show the workflow visually
2. Trigger a content brief
3. Walk through: "Submit a product brief and the AI generates email copy, social media posts for four platforms, and three lengths of product description — all version-tagged and sent for review before publishing."
4. Highlight: input validation, versioning, review gate

### Closing (30 seconds)
"Each workflow has error handling, retry logic, and logging. The AI backend is containerised and deployed on Railway with health checks. The whole system is documented, version-controlled, and built to be maintained by a team."

---

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| Separate AI backend from n8n | Keeps AI logic testable, versionable, and reusable across workflows |
| FastAPI over Flask | Async support, automatic docs, type validation via Pydantic |
| GPT-4o-mini | Cost-effective for production, fast enough for real-time |
| Retry logic on all HTTP nodes | Production systems must handle transient failures |
| Fallback responses | Users always get a response, even if AI processing fails |
| Confidence-based auto-reply | Only auto-sends when AI is confident; escalates otherwise |
| Content versioning | Every generation is tagged for audit and rollback |
| Input validation | Catches bad requests before wasting API calls |

---

## Tech Stack

- **Orchestration:** n8n (workflow automation, webhooks, routing)
- **AI Backend:** FastAPI + Python (intent extraction, triage, content generation)
- **AI Model:** OpenAI GPT-4o-mini (cost-effective, fast)
- **Hosting:** Railway (backend API)
- **Calendar:** Google Calendar API
- **Notifications:** Email (SMTP)
- **Error Handling:** Retries, fallbacks, structured logging at every step

---

## File Structure

```
supplement-ai-ops/
├── backend/
│   ├── main.py              # FastAPI application (3 AI endpoints)
│   ├── requirements.txt     # Python dependencies
│   ├── Procfile             # Railway start command
│   └── railway.json         # Railway config
├── n8n-workflows/
│   ├── workflow-1-booking.json         # Smart Consultation Booking
│   ├── workflow-2-support-triage.json  # Customer Support Triage
│   └── workflow-3-content-pipeline.json # Content Generation Pipeline
└── docs/
    ├── architecture.mermaid  # System architecture diagram
    └── README.md             # This file
```
