# ai-service/routes/interview_ai.py
from fastapi import APIRouter
from routes.recruiter_ai import generate_interview_questions, evaluate_interview, InterviewQuestionGenRequest, InterviewEvaluateRequest

router = APIRouter(prefix="/api/interview", tags=["AI Interview Assessment"])

@router.post("/generate-questions")
async def api_generate_questions(payload: InterviewQuestionGenRequest):
    return await generate_interview_questions(payload)

@router.post("/evaluate")
async def api_evaluate_interview(payload: InterviewEvaluateRequest):
    return await evaluate_interview(payload)


