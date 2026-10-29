# ai-service/routes/department_copilots.py
# Department Co-pilot: Simple Q&A chat system powered by LLMAdapter (Hugging Face / OpenAI / Gemini)

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List
from services.llm_adapter import llm

router = APIRouter(prefix="/api/copilot", tags=["Department AI Copilots"])


# ── Request / Response Models ──────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str           # "user" or "assistant"
    content: str

class CopilotAskRequest(BaseModel):
    question: str
    department: Optional[str] = "General"
    context: Optional[str] = ""         # optional extra context (e.g. employee count, dept stats)
    history: Optional[List[ChatMessage]] = []   # optional prior conversation turns


class CopilotAskResponse(BaseModel):
    answer: str
    department: str
    question: str


# ── Helper: build system prompt ────────────────────────────────────────────────

def build_system_prompt(department: str, context: str) -> str:
    base = (
        f"You are the AI Co-pilot for the {department} department inside an HRMS platform. "
        "You are friendly, concise, and helpful. You answer questions about HR policies, "
        "leave management, attendance, payroll, expenses, team management, and general workplace queries. "
        "Keep answers short and easy to understand — like a knowledgeable colleague chatting with you. "
        "Avoid jargon. If something is outside your scope, politely say so and suggest who to contact."
    )
    if context:
        base += f"\n\nAdditional context about this department:\n{context}"
    return base


# ── Main Q&A Endpoint ──────────────────────────────────────────────────────────

@router.post("/ask", response_model=CopilotAskResponse)
async def ask_copilot(payload: CopilotAskRequest):
    """
    POST /api/copilot/ask
    Simple question → answer endpoint for the Department AI Co-pilot chat.
    """
    system_prompt = build_system_prompt(
        department=payload.department or "General",
        context=payload.context or ""
    )

    # Build conversation context if history is provided
    conversation_context = ""
    if payload.history:
        for msg in payload.history[-6:]:   # use last 6 turns to keep context tight
            role_label = "User" if msg.role == "user" else "Assistant"
            conversation_context += f"{role_label}: {msg.content}\n"
        conversation_context += f"User: {payload.question}"
        full_prompt = conversation_context
    else:
        full_prompt = payload.question

    answer = await llm.generate_completion(
        prompt=full_prompt,
        system_prompt=system_prompt
    )

    return CopilotAskResponse(
        answer=answer,
        department=payload.department or "General",
        question=payload.question
    )


# ── Health / Status ────────────────────────────────────────────────────────────

@router.get("/status")
async def copilot_status():
    """Quick ping to check if co-pilot service is alive."""
    return {
        "status": "online",
        "description": "Department AI Co-pilot — Q&A mode active",
        "endpoint": "POST /api/copilot/ask"
    }
