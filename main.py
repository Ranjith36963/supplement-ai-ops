"""
AI-Powered Supplement Operations Backend
Handles: Booking Processing, Customer Support Triage
Built with FastAPI + OpenAI
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from openai import OpenAI

# ─── Logging ───
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ─── App Setup ───
app = FastAPI(
    title="Supplement AI Operations API",
    description="AI-powered booking and customer support triage for supplement businesses",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── OpenAI Client ───
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ─── Models ───

class BookingRequest(BaseModel):
    message: str
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None

class SupportRequest(BaseModel):
    message: str
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    order_id: Optional[str] = None

# ─── Health Check ───

@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "Supplement AI Operations API",
        "version": "1.0.0",
        "endpoints": {
            "booking": "/api/booking/process",
            "support": "/api/support/triage",
            "retell_call": "/api/retell/create-web-call",
            "retell_webhook": "/api/retell/webhook",
            "health": "/health"
        }
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# ─── Booking: Smart Consultation Booking ───

@app.post("/api/booking/process")
async def process_booking(request: BookingRequest):
    """
    Process natural language booking request.
    Extracts: intent, preferred date/time, health concerns, urgency.
    Returns structured booking data + personalised supplement suggestion.
    """
    logger.info(f"Booking request received: {request.message[:100]}")

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """You are a booking assistant for a health supplement company.
Extract booking details from the customer message and return ONLY valid JSON.

CLASSIFICATION RULES (very important):
- If the customer mentions ANY of: "book", "booking", "appointment", "consultation", "schedule", "slot", a specific date, or a specific time → intent MUST be "book_consultation"
- Only use "enquiry" if the customer is asking a general question with NO booking intent and NO date/time mentioned
- Use "reschedule" only if they explicitly mention changing an existing booking
- Use "cancel" only if they explicitly mention cancelling

Return JSON with these fields:
{
    "intent": "book_consultation" | "reschedule" | "cancel" | "enquiry",
    "preferred_date": "YYYY-MM-DD or null",
    "preferred_time": "HH:MM or null",
    "health_concerns": ["focus", "energy", "mood", "immune"] (list whichever apply),
    "urgency": "high" | "medium" | "low",
    "summary": "Brief summary of what the customer needs",
    "supplement_suggestion": {
        "primary": "Name of suggested supplement category",
        "reason": "Brief personalised reason based on their concerns"
    },
    "follow_up_questions": ["Any clarifying questions if details are missing"]
}

If the date/time is relative (e.g., "next Thursday"), calculate from today's date.
Today's date is """ + datetime.utcnow().strftime("%Y-%m-%d")
                },
                {"role": "user", "content": request.message}
            ],
            temperature=0.3,
            max_tokens=500
        )

        result_text = response.choices[0].message.content.strip()
        # Clean markdown fences if present
        result_text = result_text.replace("```json", "").replace("```", "").strip()
        result = json.loads(result_text)

        return {
            "status": "success",
            "booking_data": result,
            "customer_name": request.customer_name,
            "customer_email": request.customer_email,
            "processed_at": datetime.utcnow().isoformat(),
            "requires_calendar_check": result.get("intent") == "book_consultation"
        }

    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e}")
        return {
            "status": "fallback",
            "booking_data": {
                "intent": "enquiry",
                "summary": request.message,
                "health_concerns": [],
                "follow_up_questions": ["Could you please provide your preferred date and time?"]
            },
            "error": "Could not fully parse request, routed to manual review",
            "processed_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Booking processing error: {e}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


# ─── Support: Customer Support Triage & Auto-Response ───

@app.post("/api/support/triage")
async def triage_support(request: SupportRequest):
    """
    Classify customer query and generate auto-response draft.
    Categories: billing, product_question, complaint, returns, consultation, shipping, other
    Routes complex issues to appropriate team member.
    """
    logger.info(f"Support request received: {request.message[:100]}")

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """You are a customer support AI for a health supplement company.
Analyse the customer message and return ONLY valid JSON:

{
    "category": "billing" | "product_question" | "complaint" | "returns" | "consultation" | "shipping" | "dosage" | "side_effects" | "other",
    "priority": "urgent" | "high" | "medium" | "low",
    "sentiment": "positive" | "neutral" | "negative" | "angry",
    "auto_response": "A helpful, empathetic draft response to the customer (2-3 sentences)",
    "internal_notes": "Brief notes for the support team",
    "suggested_action": "auto_reply" | "escalate_to_specialist" | "escalate_to_manager" | "forward_to_billing" | "schedule_callback",
    "tags": ["relevant", "tags", "for", "analytics"],
    "confidence": 0.0 to 1.0,
    "relevant_products": ["list any products mentioned or relevant"]
}

Be empathetic and helpful. For health-related queries, always recommend consulting a healthcare professional.
Never make medical claims about supplements."""
                },
                {"role": "user", "content": request.message}
            ],
            temperature=0.3,
            max_tokens=600
        )

        result_text = response.choices[0].message.content.strip()
        result_text = result_text.replace("```json", "").replace("```", "").strip()
        result = json.loads(result_text)

        # Add routing logic
        routing = {
            "auto_reply": {"action": "send_response", "team": "automated"},
            "escalate_to_specialist": {"action": "create_ticket", "team": "product_specialist"},
            "escalate_to_manager": {"action": "create_ticket", "team": "management"},
            "forward_to_billing": {"action": "create_ticket", "team": "billing"},
            "schedule_callback": {"action": "create_callback", "team": "support_lead"}
        }

        suggested = result.get("suggested_action", "auto_reply")
        route = routing.get(suggested, routing["auto_reply"])

        return {
            "status": "success",
            "triage_data": result,
            "routing": route,
            "customer_name": request.customer_name,
            "customer_email": request.customer_email,
            "order_id": request.order_id,
            "processed_at": datetime.utcnow().isoformat(),
            "auto_reply_ready": result.get("confidence", 0) >= 0.8 and suggested == "auto_reply"
        }

    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error in triage: {e}")
        return {
            "status": "fallback",
            "triage_data": {
                "category": "other",
                "priority": "medium",
                "suggested_action": "escalate_to_specialist",
                "auto_response": "Thank you for reaching out. A team member will review your query and get back to you shortly.",
                "internal_notes": "AI triage failed - needs manual review"
            },
            "routing": {"action": "create_ticket", "team": "support_lead"},
            "processed_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Triage error: {e}")
        raise HTTPException(status_code=500, detail=f"Triage error: {str(e)}")


# ─── Global Error Handler ───

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "An internal error occurred. The request has been logged for review.",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# ─── RETELL AI: Create Web Call ───

@app.post("/api/retell/create-web-call")
async def create_retell_web_call():
    """
    Creates a Retell web call and returns the access token.
    Keeps the API key secure on the server side.
    """
    import httpx

    retell_api_key = os.getenv("RETELL_API_KEY")
    retell_agent_id = os.getenv("RETELL_AGENT_ID")

    if not retell_api_key or not retell_agent_id:
        raise HTTPException(status_code=500, detail="Retell credentials not configured")

    try:
        async with httpx.AsyncClient() as client_http:
            response = await client_http.post(
                "https://api.retellai.com/v2/create-web-call",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {retell_api_key}"
                },
                json={"agent_id": retell_agent_id},
                timeout=10.0
            )
            data = response.json()

            if response.status_code != 201 and response.status_code != 200:
                logger.error(f"Retell API error: {data}")
                raise HTTPException(status_code=response.status_code, detail="Failed to create web call")

            return {"access_token": data.get("access_token"), "call_id": data.get("call_id")}

    except httpx.RequestError as e:
        logger.error(f"Retell connection error: {e}")
        raise HTTPException(status_code=500, detail="Could not connect to Retell AI")


# ─── RETELL AI: Post-Call Webhook ───

async def forward_call_to_n8n(transcript: str, call_id: str, metadata: dict):
    """Background task: forward voice call transcript to n8n for processing."""
    import httpx

    n8n_url = os.getenv(
        "N8N_WEBHOOK_URL",
        "https://ranjith369.app.n8n.cloud/webhook/supplement-reception"
    )

    customer_name = metadata.get("customer_name", "Voice Call Customer")
    customer_email = metadata.get("customer_email", "")

    payload = {
        "message": transcript,
        "customer_name": customer_name,
        "customer_email": customer_email,
        "source": "voice_call",
        "call_id": call_id
    }

    try:
        async with httpx.AsyncClient() as http:
            resp = await http.post(n8n_url, json=payload, timeout=15.0)
            logger.info(f"n8n forwarding result: status={resp.status_code}, call_id={call_id}")
    except Exception as e:
        logger.error(f"Failed to forward call {call_id} to n8n: {e}")


@app.post("/api/retell/webhook")
async def retell_webhook(request: Request):
    """
    Receives Retell AI webhook events (call_ended, call_analyzed).
    Extracts the call transcript and forwards it to n8n for full pipeline processing
    (AI classification, Google Calendar event creation, Slack notification).
    """
    import asyncio

    body = await request.json()
    event = body.get("event", "")
    call = body.get("call", {})
    call_id = call.get("call_id", "unknown")

    logger.info(f"Retell webhook: event={event}, call_id={call_id}")

    if event != "call_ended":
        return {"status": "ignored", "event": event}

    transcript = call.get("transcript", "")
    if not transcript or len(transcript.strip()) < 10:
        logger.warning(f"Skipping call {call_id}: empty or too short transcript")
        return {"status": "skipped", "reason": "no_transcript"}

    metadata = call.get("metadata", {})

    asyncio.create_task(forward_call_to_n8n(transcript, call_id, metadata))

    return {"status": "accepted", "call_id": call_id}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
