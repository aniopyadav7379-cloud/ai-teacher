"""
LESSON PLANNER (spec section 8): builds a structured lesson object from
either uploaded material (grounded via RAG) or a bare topic, respecting the
learner profile and time budget.
"""
from __future__ import annotations
from dataclasses import dataclass, field

from backend.services.llm.factory import get_llm_provider
from backend.services.rag.retriever import get_grounded_context
from backend.prompts.planning import LESSON_PLANNER_SYSTEM, build_lesson_planner_prompt


@dataclass
class PlannedQuestion:
    question_type: str
    prompt: str
    options: list[str] | None
    correct_answer: str
    difficulty: str


@dataclass
class PlannedConcept:
    concept: str
    importance: str
    estimated_minutes: int
    explanation_depth: str
    prerequisite: str | None
    explanation: str
    example: str
    analogy: str
    source_citation: str | None
    visual_type: str
    question: PlannedQuestion


@dataclass
class LessonPlan:
    lesson_title: str
    learning_objectives: list[str]
    grounded_in_material: bool
    concepts: list[PlannedConcept] = field(default_factory=list)


async def plan_lesson(
    *,
    topic: str | None,
    material_ids: list[str],
    learner_level: str,
    goal: str,
    language: str,
    teaching_style: str,
    available_minutes: int,
    depth: str,
) -> LessonPlan:
    llm = get_llm_provider()

    grounded_context = None
    subject_summary = topic or "the uploaded material"
    if material_ids:
        ctx = await get_grounded_context(material_ids, topic or goal or "overview key concepts", top_k=8)
        if ctx.grounded:
            grounded_context = ctx.context_text

    prompt = build_lesson_planner_prompt(
        topic_or_material_summary=subject_summary,
        learner_level=learner_level,
        goal=goal,
        language=language,
        teaching_style=teaching_style,
        available_minutes=available_minutes,
        depth=depth,
        grounded_context=grounded_context,
    )
    data = await llm.complete_json(LESSON_PLANNER_SYSTEM, prompt, max_tokens=4000, temperature=0.4)

    concepts = []
    for c in data.get("concepts", []):
        q = c.get("question") or {}
        concepts.append(
            PlannedConcept(
                concept=c["concept"],
                importance=c.get("importance", "core"),
                estimated_minutes=int(c.get("estimated_minutes", 5)),
                explanation_depth=c.get("explanation_depth", depth),
                prerequisite=c.get("prerequisite"),
                explanation=c.get("explanation", ""),
                example=c.get("example", ""),
                analogy=c.get("analogy", ""),
                source_citation=c.get("source_citation"),
                visual_type=c.get("visual_type", "none"),
                question=PlannedQuestion(
                    question_type=q.get("question_type", "conceptual"),
                    prompt=q.get("prompt", ""),
                    options=q.get("options"),
                    correct_answer=q.get("correct_answer", ""),
                    difficulty=q.get("difficulty", "medium"),
                ),
            )
        )

    return LessonPlan(
        lesson_title=data.get("lesson_title", subject_summary),
        learning_objectives=data.get("learning_objectives", []),
        grounded_in_material=bool(data.get("grounded_in_material", bool(grounded_context))),
        concepts=concepts,
    )
