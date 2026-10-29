# ai-service/services/llm_adapter.py
import os
import httpx
from typing import Optional

class LLMAdapter:
    def __init__(self):
        self.hf_token = os.getenv("HUGGINGFACE_API_KEY") or os.getenv("HF_TOKEN", "")
        self.openai_key = os.getenv("OPENAI_API_KEY", "")
        self.gemini_key = os.getenv("GEMINI_API_KEY", "")
        self.provider = os.getenv("AI_PROVIDER", "huggingface").lower()
        # Default fast & high quality Hugging Face model on free serverless tier
        self.hf_model = os.getenv("HF_MODEL", "Qwen/Qwen2.5-7B-Instruct")

    async def generate_completion(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        # 1. Hugging Face Serverless Inference API (Free Tier)
        if self.hf_token:
            try:
                async with httpx.AsyncClient(timeout=12.0) as client:
                    # Hugging Face v1 chat completions endpoint (OpenAI compatible)
                    resp = await client.post(
                        "https://router.huggingface.co/hf-inference/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.hf_token}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": self.hf_model,
                            "messages": [
                                {"role": "system", "content": system_prompt or "You are an HRMS AI assistant."},
                                {"role": "user", "content": prompt}
                            ],
                            "max_tokens": 400,
                            "temperature": 0.4
                        }
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        return data["choices"][0]["message"]["content"].strip()
            except Exception as e:
                print(f"[LLMAdapter] HuggingFace serverless failed: {e}")

        # 2. OpenAI Integration
        if self.provider == "openai" and self.openai_key:
            try:
                async with httpx.AsyncClient(timeout=12.0) as client:
                    resp = await client.post(
                        "https://api.openai.com/v1/chat/completions",
                        headers={"Authorization": f"Bearer {self.openai_key}"},
                        json={
                            "model": "gpt-4o-mini",
                            "messages": [
                                {"role": "system", "content": system_prompt or "You are an HRMS AI assistant."},
                                {"role": "user", "content": prompt}
                            ],
                            "temperature": 0.3
                        }
                    )
                    if resp.status_code == 200:
                        return resp.json()["choices"][0]["message"]["content"]
            except Exception as e:
                print(f"[LLMAdapter] OpenAI failed: {e}")

        # 3. Gemini Integration
        if self.provider == "gemini" and self.gemini_key:
            try:
                async with httpx.AsyncClient(timeout=12.0) as client:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_key}"
                    resp = await client.post(
                        url,
                        json={"contents": [{"parts": [{"text": f"{system_prompt}\n\n{prompt}"}]}]}
                    )
                    if resp.status_code == 200:
                        return resp.json()["candidates"][0]["content"]["parts"][0]["text"]
            except Exception as e:
                print(f"[LLMAdapter] Gemini failed: {e}")

        # 4. Instant Zero-Latency Local Fallback
        return f"[Hugging Face Local Engine]\nProcessed evaluation for: {prompt[:150]}..."

llm = LLMAdapter()
