import json
import pytest

from backend.services.lesson import planner as planner_module

FAKE_PLAN_JSON = json.dumps({
    "lesson_title": "Introduction to Ohm's Law",
    "learning_objectives": ["Understand V=IR", "Apply Ohm's law to simple circuits"],
    "grounded_in_material": False,
    "concepts": [
        {
            "concept": "Ohm's Law",
            "importance": "core",
            "estimated_minutes": 8,
            "explanation_depth": "standard",
            "prerequisite": None,
            "explanation": "Ohm's law relates voltage, current, and resistance: V = I x R.",
            "example": "If V=10V and R=5ohm, then I=2A.",
            "analogy": "Voltage is like water pressure, current is flow, resistance is pipe narrowness.",
            "source_citation": None,
            "visual_type": "equation",
            "question": {
                "question_type": "conceptual",
                "prompt": "What happens to current if resistance increases while voltage stays constant?",
                "options": None,
                "correct_answer": "Current decreases",
                "difficulty": "medium",
            },
        }
    ],
})


class FakeLLM:
    async def complete_json(self, system_prompt, user_prompt, *, max_tokens=1500, temperature=0.2):
        return json.loads(FAKE_PLAN_JSON)


@pytest.mark.asyncio
async def test_plan_lesson_builds_structured_plan(monkeypatch):
    monkeypatch.setattr(planner_module, "get_llm_provider", lambda: FakeLLM())

    plan = await planner_module.plan_lesson(
        topic="Ohm's Law",
        material_ids=[],
        learner_level="beginner",
        goal="Pass my physics exam",
        language="en",
        teaching_style="socratic",
        available_minutes=20,
        depth="standard",
    )

    assert plan.lesson_title == "Introduction to Ohm's Law"
    assert len(plan.concepts) == 1
    concept = plan.concepts[0]
    assert concept.concept == "Ohm's Law"
    assert concept.question.correct_answer == "Current decreases"
    assert plan.grounded_in_material is False
