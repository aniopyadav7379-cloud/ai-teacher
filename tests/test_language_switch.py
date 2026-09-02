import json
import pytest

from backend.database.session import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import models
from backend.services.lesson import translator as translator_module


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    s = Session()
    yield s
    s.close()


def _build_lesson(db):
    user = models.User(email="a@b.com", hashed_password="x")
    db.add(user); db.flush()
    session = models.LearningSession(user_id=user.id, mode="topic", topic="Ohm's Law", language="en")
    db.add(session); db.flush()
    lesson = models.Lesson(session_id=session.id, title="Ohm's Law", learner_level="beginner", language="en",
                            duration_minutes=20, current_concept_index=1)
    db.add(lesson); db.flush()

    c0 = models.LessonConcept(lesson_id=lesson.id, order_index=0, concept="Voltage",
                               explanation="Voltage is potential difference.", example="ex0", analogy="an0", status="mastered")
    c1 = models.LessonConcept(lesson_id=lesson.id, order_index=1, concept="Current",
                               explanation="Current is charge flow.", example="ex1", analogy="an1", status="pending")
    db.add_all([c0, c1]); db.flush()

    q0 = models.Question(concept_id=c0.id, question_type="conceptual", prompt="What is voltage?", correct_answer="a")
    q1 = models.Question(concept_id=c1.id, question_type="conceptual", prompt="What is current?", correct_answer="b")
    db.add_all([q0, q1]); db.commit()
    return lesson, c0, c1, q0, q1


FAKE_TRANSLATION = None  # set per-test


class FakeLLM:
    async def complete_json(self, system_prompt, user_prompt, *, max_tokens=1500, temperature=0.2):
        return FAKE_TRANSLATION


@pytest.mark.asyncio
async def test_switch_language_only_translates_remaining_concepts(db, monkeypatch):
    global FAKE_TRANSLATION
    lesson, c0, c1, q0, q1 = _build_lesson(db)

    FAKE_TRANSLATION = {
        "concepts": [
            {
                "id": c1.id,
                "explanation": "करंट आवेश का प्रवाह है।",
                "example": "उदाहरण1",
                "analogy": "उपमा1",
                "question_prompt": "करंट क्या है?",
                "question_options": None,
            }
        ]
    }
    monkeypatch.setattr(translator_module, "get_llm_provider", lambda: FakeLLM())

    updated = await translator_module.switch_lesson_language(db, lesson, "hi")

    assert updated.language == "hi"
    # Completed concept (index 0, before current_concept_index) is untouched.
    db.refresh(c0)
    assert c0.explanation == "Voltage is potential difference."
    # Remaining concept (index 1, current) IS translated.
    db.refresh(c1)
    assert c1.explanation == "करंट आवेश का प्रवाह है।"
    db.refresh(q1)
    assert q1.prompt == "करंट क्या है?"
    # Lesson state (which concept we're on) is untouched by the language switch.
    assert updated.current_concept_index == 1


@pytest.mark.asyncio
async def test_switch_language_is_noop_when_already_target_language(db, monkeypatch):
    lesson, *_ = _build_lesson(db)
    calls = {"n": 0}

    class CountingLLM:
        async def complete_json(self, *a, **kw):
            calls["n"] += 1
            return {}

    monkeypatch.setattr(translator_module, "get_llm_provider", lambda: CountingLLM())
    result = await translator_module.switch_lesson_language(db, lesson, "en")
    assert calls["n"] == 0
    assert result.language == "en"
