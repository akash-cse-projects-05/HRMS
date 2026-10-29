import uvicorn
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time

from config import PORT, HOST, INTERNAL_SECRET
from routes.recruiter_ai import router as recruiter_router
from routes.interview_ai import router as interview_router
from routes.department_copilots import router as copilot_router
from routes.policy_rag import router as policy_router

app = FastAPI(
    title="HRMS Enterprise AI Microservice",
    description="Dedicated AI microservice handling AI Candidate Screening & Interview Scoring, Department Copilots, and Policy RAG Assistant.",
    version="1.0.0"
)

# Enable CORS for local development and Node.js backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Optional Header Authentication Middleware
@app.middleware("http")
async def verify_secret_and_measure_time(request: Request, call_next):
    # Allow health checks and OpenAPI docs without secret
    open_paths = ["/", "/health", "/docs", "/openapi.json", "/redoc"]
    if request.url.path not in open_paths:
        secret = request.headers.get("X-Internal-Secret")
        # In development, allow if secret matches or if header not strictly enforced
        if secret and secret != INTERNAL_SECRET:
            return JSONResponse(status_code=403, content={"detail": "Forbidden: Invalid AI Service Secret"})

    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}s"
    return response

# Register API Routers
app.include_router(recruiter_router)
app.include_router(interview_router)
app.include_router(copilot_router)
app.include_router(policy_router)

@app.get("/")
async def root():
    return {
        "service": "HRMS Enterprise AI Microservice",
        "status": "online",
        "version": "1.0.0",
        "docs_url": "/docs"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "hrms-ai-service"
    }

if __name__ == "__main__":
    print(f"🚀 Starting HRMS AI Microservice on http://{HOST}:{PORT}")
    uvicorn.run("app:app", host=HOST, port=PORT, reload=True)
