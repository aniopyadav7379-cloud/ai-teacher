TRANSLATOR_SYSTEM = """You translate teaching content for an in-progress lesson. \
Preserve the pedagogical meaning exactly — do not simplify, shorten, or add \
content, and do not translate proper nouns, formulas, code, or numbers. \
Keep the same tone and teaching style as the original."""


def build_translation_prompt(*, target_language: str, concepts_json: str) -> str:
    return f"""Translate every text field below into {target_language}. This is \
mid-lesson content for a student already partway through — meaning must stay \
identical, only the language changes.

Concepts (JSON array):
{concepts_json}

Return a JSON object of the exact shape {{"concepts": [...]}}, where the array \
has the same length and order as the input, each item keeping its original \
"id" unchanged, with "explanation", "example", "analogy", "question_prompt", \
and "question_options" translated into {target_language}."""
