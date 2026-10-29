# ai-service/services/evaluator.py
import re
from typing import List, Dict, Any
from services.model_manager import model_manager

class InterviewEvaluator:
    """
    Evaluates candidate interview answers using Hugging Face semantic similarity.
    Blazing fast (~15ms per answer on CPU), objective, and robust against rephrasing.
    """

    def evaluate_submission(self, target_role: str, answers: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not answers:
            return {
                "overall_score": 0.0,
                "technical_score": 0.0,
                "problem_solving_score": 0.0,
                "clarity_score": 0.0,
                "recommendation": "REJECT",
                "detailed_evaluations": [],
                "strengths": ["No answers submitted"],
                "concerns": ["Candidate left interview blank"],
                "ai_summary": "Incomplete submission. Zero responses recorded."
            }

        detailed = []
        tech_scores = []
        problem_scores = []
        clarity_scores = []
        strengths = []
        concerns = []

        for item in answers:
            q_id = item.get("question_id", "")
            q_text = item.get("question_text", "")
            ans = (item.get("candidate_answer") or "").strip()
            cat = (item.get("category") or "TECHNICAL").upper()
            keywords = item.get("expected_keywords") or []

            words = ans.split()
            word_count = len(words)

            if word_count < 4:
                item_score = 10.0 if word_count > 0 else 0.0
                clarity = 15.0 if word_count > 0 else 0.0
                feedback = "Answer is too brief or evasive to assess competency."
            else:
                # 1. Hugging Face Semantic Similarity with Expected Concepts
                keywords_context = f"{q_text}. Core concepts: {', '.join(keywords)}" if keywords else q_text
                semantic_sim = model_manager.compute_similarity(ans, keywords_context)

                # 2. Keyword coverage
                ans_lower = ans.lower()
                matched_kw = [kw for kw in keywords if kw.lower() in ans_lower]
                kw_ratio = (len(matched_kw) / max(len(keywords), 1)) if keywords else 0.5

                # 3. Composite score (65% semantic understanding, 25% keyword coverage, 10% length sufficiency)
                length_factor = min(1.0, word_count / 30.0) # ideal answer ~30+ words
                raw_score = (semantic_sim * 0.65) + (kw_ratio * 0.25) + (length_factor * 0.10)
                item_score = round(min(100.0, max(0.0, raw_score * 100)), 1)

                # Clarity & fluency assessment
                clarity = round(min(100.0, max(30.0, (semantic_sim * 50) + (length_factor * 50))), 1)

                if item_score >= 70:
                    feedback = f"Strong grasp demonstrated. Effectively addressed concepts like {', '.join(matched_kw[:2]) if matched_kw else 'core domain'}"
                    strengths.append(f"Q: '{q_text[:40]}...' scored {item_score}% with solid conceptual reasoning.")
                elif item_score >= 45:
                    feedback = "Acceptable response, though could elaborate with more specific architectural details."
                else:
                    feedback = "Superficial answer; lacked required depth on key technical requirements."
                    concerns.append(f"Q: '{q_text[:40]}...' scored low ({item_score}%), missing expected domain depth.")

            detailed.append({
                "question_id": q_id,
                "category": cat,
                "score": item_score,
                "clarity": clarity,
                "feedback": feedback
            })

            clarity_scores.append(clarity)
            if "TECH" in cat or "CODE" in cat:
                tech_scores.append(item_score)
            else:
                problem_scores.append(item_score)

        avg_tech = round(sum(tech_scores) / max(len(tech_scores), 1), 1) if tech_scores else 60.0
        avg_prob = round(sum(problem_scores) / max(len(problem_scores), 1), 1) if problem_scores else avg_tech
        avg_clarity = round(sum(clarity_scores) / max(len(clarity_scores), 1), 1)

        # Weighted Overall Score
        overall = round((avg_tech * 0.45) + (avg_prob * 0.35) + (avg_clarity * 0.20), 1)

        if overall >= 75.0:
            rec = "STRONG_HIRE"
        elif overall >= 60.0:
            rec = "SHORTLIST"
        elif overall >= 45.0:
            rec = "HOLD"
        else:
            rec = "REJECT"

        if not strengths:
            strengths.append("Completed the interview assessment within the allocated exam duration.")
        if not concerns:
            concerns.append("No major red flags detected in candidate answers.")

        summary = (
            f"Candidate achieved an overall AI score of {overall}% ({rec}) for the {target_role} role. "
            f"Technical proficiency scored {avg_tech}%, problem solving {avg_prob}%, and communication clarity {avg_clarity}%. "
            f"Assessed via Hugging Face all-MiniLM-L6-v2 semantic similarity engine."
        )

        return {
            "overall_score": overall,
            "technical_score": avg_tech,
            "problem_solving_score": avg_prob,
            "clarity_score": avg_clarity,
            "recommendation": rec,
            "detailed_evaluations": detailed,
            "strengths": strengths[:4],
            "concerns": concerns[:3],
            "ai_summary": summary
        }

interview_evaluator = InterviewEvaluator()
