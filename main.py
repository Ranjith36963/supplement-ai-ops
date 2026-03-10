"""
AI-Powered Supplement Operations Backend
Handles: Booking Processing, Customer Support Triage, Content Generation
Built with FastAPI + OpenAI
"""

import os
import json
import logging
from datetime import datetime, timedelta
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
    description="AI-powered booking, customer support triage, and content generation for supplement businesses",
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

class ContentRequest(BaseModel):
    brief: str
    product_category: Optional[str] = "focus"  # focus, energy, mood, immune
    content_types: Optional[list] = ["email", "social_media", "product_description"]
    tone: Optional[str] = "professional"

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
            "content": "/api/content/generate",
            "retell_call": "/api/retell/create-web-call",
            "health": "/health"
        }
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# ─── WORKFLOW 1: Smart Consultation Booking ───

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
Extract booking details from the customer message and return ONLY valid JSON with these fields:

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


# ─── WORKFLOW 2: Customer Support Triage & Auto-Response ───

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


# ─── WORKFLOW 3: Content Generation Pipeline ───

@app.post("/api/content/generate")
async def generate_content(request: ContentRequest):
    """
    Generate multiple content variants from a brief.
    Outputs: email copy, social media posts, product descriptions.
    Each variant is versioned and formatted for review.
    """
    logger.info(f"Content request received: {request.brief[:100]}")

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"""You are a content specialist for a health supplement company.
Generate content variants based on the brief provided. Return ONLY valid JSON:

{{
    "content_variants": {{
        "email": {{
            "subject_line": "Compelling email subject",
            "preview_text": "Preview text for email clients (50 chars)",
            "body": "Full email body copy (HTML-friendly, 150-200 words)",
            "cta": "Call-to-action text"
        }},
        "social_media": {{
            "instagram": "Instagram caption with relevant hashtags (under 200 words)",
            "twitter": "Tweet-length post (under 280 chars)",
            "facebook": "Facebook post (100-150 words)",
            "linkedin": "Professional LinkedIn post (150-200 words)"
        }},
        "product_description": {{
            "short": "Short product description (50 words)",
            "medium": "Medium description (100 words)",
            "long": "Detailed description (200 words)"
        }}
    }},
    "meta": {{
        "target_audience": "Identified target audience",
        "key_benefits": ["benefit1", "benefit2", "benefit3"],
        "tone_used": "{request.tone}",
        "seo_keywords": ["keyword1", "keyword2", "keyword3"]
    }}
}}

Product category focus: {request.product_category}
Tone: {request.tone}
IMPORTANT: Never make medical claims. Use phrases like "may help support", "designed to help".
Follow UK advertising standards for supplements."""
                },
                {"role": "user", "content": request.brief}
            ],
            temperature=0.7,
            max_tokens=1500
        )

        result_text = response.choices[0].message.content.strip()
        result_text = result_text.replace("```json", "").replace("```", "").strip()
        result = json.loads(result_text)

        # Add versioning metadata
        version_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

        return {
            "status": "success",
            "content": result,
            "version_id": version_id,
            "brief": request.brief,
            "product_category": request.product_category,
            "generated_at": datetime.utcnow().isoformat(),
            "review_status": "pending_approval",
            "content_types_generated": list(result.get("content_variants", {}).keys())
        }

    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error in content gen: {e}")
        return {
            "status": "fallback",
            "error": "Content generation produced invalid format. Retrying recommended.",
            "brief": request.brief,
            "processed_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Content generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Content generation error: {str(e)}")


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


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
