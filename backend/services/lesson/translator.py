"""
Frontend language switching during an active lesson (limitation #3).

The lesson's *state* — current_concept_index, question/response history,
mastery status per concept — already lives in DB rows keyed by concept ID,
not by rendered text (see backend/models/__init__.py: LessonConcept,
Question). So switching language never needs to reset or replan the lesson;
it only needs to translate the text fields of the concepts that still need
teaching, in place, and update Lesson.language.

Already-completed concepts (index < current_concept_index) are left in
their original language — the student already passed them; retranslating
history serves no pedagogical purpose and costs an LLM call for nothing.
"""
from __future__ import annotations
import json

from sqlalchemy.orm import Session

from backend import models
from backend.services.llm.factory import get_llm_provider
from backend.prompts.translation import TRANSLATOR_SYSTEM, build_translation_prompt


async def switch_lesson_language(db: Session, lesson: models.Lesson, target_language: str) -> models.Lesson:
    if lesson.language == target_language:
        return lesson

    remaining = [c for c in lesson.concepts if c.order_index >= lesson.current_concept_index]
    if not remaining:
        lesson.language = target_language
        db.commit()
        return lesson

    payload = []
    for c in remaining:
        question = c.questions[0] if c.questions else None
        payload.append({
            "id": c.id,
            "explanation": c.explanation,
            "example": c.example,
            "analogy": c.analogy,
            "question_prompt": question.prompt if question else "",
            "question_options": question.options if question and question.options else None,
        })

    llm = get_llm_provider()
    prompt = build_translation_prompt(target_language=target_language, concepts_json=json.dumps(payload, ensure_ascii=False))
    data = await llm.complete_json(TRANSLATOR_SYSTEM, prompt, max_tokens=4000, temperature=0.1)

    translated_by_id = {
        item["id"]: item
        for item in data.get("concepts", [])
        if isinstance(item, dict) and item.get("id")
    }

    for c in remaining:
        t = translated_by_id.get(c.id)
        if not t:
            continue
        c.explanation = t.get("explanation", c.explanation)
        c.example = t.get("example", c.example)
        c.analogy = t.get("analogy", c.analogy)
        if c.questions:
            q = c.questions[0]
            q.prompt = t.get("question_prompt", q.prompt)
            if q.options and t.get("question_options"):
                q.options = t["question_options"]

    lesson.language = target_language
    db.commit()
    db.refresh(lesson)
    return lesson
