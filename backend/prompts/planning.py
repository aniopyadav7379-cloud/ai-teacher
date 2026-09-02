LESSON_PLANNER_SYSTEM = """You are an expert curriculum designer and master teacher. \
You design lesson plans that a real AI teacher will follow step by step. \
Always tailor depth and pacing to the learner's level, goal, available time, and \
preferred teaching style. If source material is provided, ground every concept \
in it and never invent facts the material doesn't support; if no material is \
provided, teach from sound general knowledge of the subject."""


def build_lesson_planner_prompt(
    *,
    topic_or_material_summary: str,
    learner_level: str,
    goal: str,
    language: str,
    teaching_style: str,
    available_minutes: int,
    depth: str,
    grounded_context: str | None,
) -> str:
    time_guidance = {
        available_minutes <= 5: "Focus ONLY on the single most essential concept. 1 concept max.",
        5 < available_minutes <= 20: "Cover 2-4 key concepts with one example and one question each.",
        20 < available_minutes <= 60: "Cover 4-7 concepts with deeper explanation, multiple examples, and checkpoint questions.",
        available_minutes > 60: "Design a multi-session plan: break into logical sessions of ~45-60 min each, "
                                 "each with its own concept set, and include spaced revision.",
    }[True]

    grounding_block = (
        f"\n\nSOURCE MATERIAL (ground the lesson in this; cite page numbers where given):\n{grounded_context}"
        if grounded_context
        else "\n\nNo source material was uploaded — teach from general subject knowledge."
    )

    return f"""Design a lesson plan for:

Topic / Material: {topic_or_material_summary}
Learner level: {learner_level}
Learning goal: {goal}
Language: {language}
Teaching style: {teaching_style}
Available time: {available_minutes} minutes
Desired depth: {depth}

TIME BUDGET RULE: {time_guidance}
{grounding_block}

Return a JSON object with this exact shape:
{{
  "lesson_title": "string",
  "learning_objectives": ["string", ...],
  "grounded_in_material": true/false,
  "concepts": [
    {{
      "concept": "string",
      "importance": "core" | "supporting" | "optional",
      "estimated_minutes": number,
      "explanation_depth": "essential" | "standard" | "deep",
      "prerequisite": "string or null",
      "explanation": "the actual teaching explanation, 3-6 sentences, in {language}",
      "example": "a concrete worked example, in {language}",
      "analogy": "a relatable analogy for this concept, in {language}",
      "source_citation": "e.g. 'Page 12' or null if not grounded",
      "visual_type": "equation" | "diagram" | "graph" | "code" | "timeline" | "labeled_diagram" | "none",
      "question": {{
        "question_type": "mcq" | "conceptual" | "short_answer" | "problem_solving" | "application" | "explain",
        "prompt": "string, in {language}",
        "options": ["string", ...] or null,
        "correct_answer": "string",
        "difficulty": "easy" | "medium" | "hard"
      }}
    }}
  ]
}}"""
