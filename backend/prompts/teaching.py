REEXPLAIN_SYSTEM = """You are a patient, encouraging teacher. A student has a \
specific misconception. Re-teach the concept in a genuinely DIFFERENT way than \
before — a new analogy, a new example, simpler language — so repeating the \
same explanation doesn't just fail again. Never say simply 'wrong'; build \
understanding from where the student actually is."""


def build_reexplain_prompt(
    *,
    concept: str,
    original_explanation: str,
    original_analogy: str,
    misconception: str,
    learner_level: str,
    language: str,
) -> str:
    return f"""The student has this misconception about "{concept}":
{misconception}

Their original explanation was: {original_explanation}
Their original analogy was: {original_analogy}

Re-explain the concept for a {learner_level} learner, using a DIFFERENT analogy \
and a DIFFERENT concrete example than before, directly addressing the \
misconception. Write in {language}.

Return a JSON object:
{{
  "reexplanation": "string, 3-6 sentences",
  "new_analogy": "string, must differ substantially from the original analogy",
  "new_example": "string",
  "followup_question": {{
    "question_type": "mcq" | "conceptual" | "short_answer" | "application" | "explain",
    "prompt": "string, slightly easier than before, targeting exactly this misconception",
    "options": ["string", ...] or null,
    "correct_answer": "string",
    "difficulty": "easy" | "medium"
  }}
}}"""


QUESTION_GEN_SYSTEM = """You generate teaching-appropriate questions that check \
real understanding, not just recall. Match difficulty to learner level and \
lesson stage."""


def build_question_prompt(*, concept: str, learner_level: str, difficulty: str, question_type: str, language: str) -> str:
    return f"""Generate one {question_type} question about "{concept}" for a \
{learner_level} learner, difficulty: {difficulty}, in {language}.

Return JSON:
{{
  "prompt": "string",
  "options": ["string", ...] or null,
  "correct_answer": "string",
  "difficulty": "{difficulty}"
}}"""


ASSESSMENT_SYSTEM = """You are generating a final lesson assessment summary. \
Be honest and specific: identify exactly which concepts were mastered and \
which need revision, based on the student's actual response history."""


def build_assessment_prompt(*, lesson_title: str, concept_results: str, language: str) -> str:
    return f"""Lesson: {lesson_title}

Per-concept results (concept, score 0-1, misconceptions seen):
{concept_results}

Generate a final assessment. Return JSON:
{{
  "overall_score": number 0-1,
  "strong_areas": ["concept", ...],
  "weak_areas": ["concept", ...],
  "misconceptions": ["string", ...],
  "recommendation": "2-4 sentences of specific, actionable next-step advice, in {language}"
}}"""


VISUAL_PLANNER_SYSTEM = """You determine the correct visual representation for \
a concept based on its subject, and produce a compact spec another renderer \
can use. Do not attach decorative/random images — every visual must directly \
support understanding."""


def build_visual_prompt(*, subject: str, concept: str, explanation: str) -> str:
    return f"""Subject: {subject}
Concept: {concept}
Explanation: {explanation}

Choose the best visual type and produce a rendering spec. Return JSON:
{{
  "visual_type": "equation" | "diagram" | "graph" | "code" | "timeline" | "labeled_diagram" | "none",
  "title": "string",
  "spec": {{
     "description": "plain-language description of exactly what the visual should show",
     "elements": ["string", ...]
  }}
}}"""


RECOMMENDATION_SYSTEM = """You recommend what a student should learn or revise \
next, based on their assessment results and overall profile. Be concrete and \
prioritized, not generic."""


def build_learning_path_prompt(*, subject: str, learner_level: str, weak_concepts: str, goal: str) -> str:
    return f"""Subject: {subject}
Learner level: {learner_level}
Known weak concepts: {weak_concepts}
Goal: {goal}

Generate a prerequisite-ordered learning path (5-10 topics) toward the goal, \
accounting for the weak concepts (insert revision nodes where needed).

Return JSON:
{{
  "path": [
    {{"topic": "string", "prerequisite_of": "string or null", "reason": "string"}}
  ]
}}"""
