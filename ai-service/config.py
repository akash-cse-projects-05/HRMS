import os
from dotenv import load_dotenv

load_dotenv()

PORT = int(os.getenv("AI_SERVICE_PORT", "5001"))
HOST = os.getenv("AI_SERVICE_HOST", "127.0.0.1")
INTERNAL_SECRET = os.getenv("AI_SERVICE_SECRET", "hrms-internal-secret-2026")

# Hugging Face Primary Model Configuration (Free Serverless Tier & Local Embeddings)
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY") or os.getenv("HF_TOKEN", "")
HF_MODEL = os.getenv("HF_MODEL", "Qwen/Qwen2.5-7B-Instruct") # Ultra-fast top-tier Hugging Face instruct model
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2") # Hugging Face sentence-transformers
AI_PROVIDER = os.getenv("AI_PROVIDER", "huggingface") # "huggingface" by default

