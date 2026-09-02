TOPIC_ANALYZER_SYSTEM = """You analyze a raw learning request and classify it \
so the rest of the system can plan appropriately."""

def build_topic_analysis_prompt(topic: str) -> str:
    return f"""Analyze this learning request: "{topic}"

Return JSON:
{{
  "subject": "e.g. Physics, Programming, Mathematics, History, Biology, General",
  "suggested_level": "beginner" | "intermediate" | "advanced",
  "scope": "narrow" | "broad",
  "clarifying_note": "one sentence noting anything ambiguous, or empty string"
}}"""
