// HRMS/services/aiService.js
// Adapter module bridging Node.js / Express routes with the Python FastAPI ai-service

const AI_SERVICE_URL = process.env.AI_SERVICE_URL || "http://127.0.0.1:5001";
const AI_SERVICE_SECRET = process.env.AI_SERVICE_SECRET || "hrms-internal-secret-2026";

/**
 * Generic caller to Python AI microservice with timeout and error handling
 */
async function callAIService(endpoint, payload, method = "POST") {
  const url = `${AI_SERVICE_URL}${endpoint}`;
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 45000); // 45s timeout for local embedding inference

    const options = {
      method,
      headers: {
        "Content-Type": "application/json",
        "X-Internal-Secret": AI_SERVICE_SECRET,
      },
      signal: controller.signal,
    };

    if (method === "POST" && payload) {
      options.body = JSON.stringify(payload);
    }

    const response = await fetch(url, options);
    clearTimeout(timeout);

    if (!response.ok) {
      const errBody = await response.json().catch(() => ({}));
      throw new Error(errBody.detail || `AI Service error: ${response.status} ${response.statusText}`);
    }

    return await response.json();
  } catch (err) {
    if (err.name === "AbortError") {
      console.error(`[AI Service Timeout]: ${endpoint} exceeded 10s`);
      throw new Error("AI Service timed out. Please try again.");
    }
    console.error(`[AI Service Failure] ${endpoint}:`, err.message);
    throw err;
  }
}

module.exports = {
  // Health
  checkHealth: () => callAIService("/health", null, "GET"),

  // Recruiter & Candidate Interview Assessment
  screenResumeAI: (data) => callAIService("/api/recruiter/screen", data),
  generateInterviewQuestionsAI: (data) => callAIService("/api/recruiter/generate-questions", data),
  evaluateInterviewAI: (data) => callAIService("/api/recruiter/evaluate-interview", data),

  // Department AI Co-pilot Q&A
  askCopilot: (data) => callAIService("/api/copilot/ask", data),
  copilotStatus: () => callAIService("/api/copilot/status", null, "GET"),

  // Policy RAG Assistant
  queryPolicyRAG: (data) => callAIService("/api/policy/query", data),
  ingestPolicyDoc: (data) => callAIService("/api/policy/ingest", data),
  uploadPolicyPDFAI: async (fileBuffer, fileName, title, category, tenantId) => {
    const formData = new FormData();
    const blob = new Blob([fileBuffer], { type: "application/pdf" });
    formData.append("file", blob, fileName);
    formData.append("title", title);
    formData.append("category", category || "General");
    formData.append("tenant_id", tenantId || "default");

    const url = `${AI_SERVICE_URL}/api/policy/upload-pdf`;
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 60000); // 60s for 50-page PDF parsing & vectorization

    try {
      const response = await fetch(url, {
        method: "POST",
        headers: {
          "X-Internal-Secret": AI_SERVICE_SECRET
        },
        body: formData,
        signal: controller.signal
      });
      clearTimeout(timeout);

      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || `AI microservice returned HTTP ${response.status}`);
      }
      return await response.json();
    } catch (err) {
      clearTimeout(timeout);
      console.error("[uploadPolicyPDFAI Failure]:", err.message);
      throw err;
    }
  }
};
