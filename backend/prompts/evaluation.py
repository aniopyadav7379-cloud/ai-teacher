EVALUATOR_SYSTEM = """You are an expert teacher evaluating a student's answer. \
You are precise, fair, and diagnostic: your job is not just to grade but to \
understand WHY an answer is wrong, so the teaching can adapt. Never be harsh; \
frame findings constructively."""


def build_evaluation_prompt(
    *,
    concept: str,
    question_prompt: str,
    correct_answer: str,
    student_answer: str,
    language: str,
) -> str:
    return f"""Evaluate this student's answer.

Concept being tested: {concept}
Question: {question_prompt}
Reference correct answer: {correct_answer}
Student's answer: {student_answer}

Classify and diagnose it. Return a JSON object with this exact shape:
{{
  "correct": true/false,
  "classification": "correct" | "partially_correct" | "incorrect" | "uncertain",
  "score": number between 0 and 1,
  "misconception": "a specific, plain-language description of the misconception, or null if none",
  "misconception_type": "conceptual" | "missing_prerequisite" | "weak_understanding" | "careless_error" | "terminology_confusion" | "calculation_error" | null,
  "severity": "low" | "medium" | "high" | null,
  "reasoning": "1-2 sentences explaining your judgment, in {language}",
  "recommended_action": "advance" | "reinforce" | "clarify_gap" | "re_explain_with_analogy" | "re_explain_with_example"
}}"""
