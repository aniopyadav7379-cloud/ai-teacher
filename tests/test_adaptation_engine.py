from backend.services.evaluation.evaluator import EvaluationResult
from backend.services.adaptation.engine import decide_next_action, AdaptationAction


def _eval(classification, score=0.5, misconception=None):
    return EvaluationResult(
        correct=classification == "correct",
        classification=classification,
        score=score,
        misconception=misconception,
        misconception_type=None,
        severity=None,
        reasoning="test",
        recommended_action="advance",
    )


def test_correct_strong_confidence_increases_difficulty():
    decision = decide_next_action(_eval("correct", score=0.95), consecutive_struggles=0)
    assert decision.action == AdaptationAction.ADVANCE_INCREASE_DIFFICULTY


def test_correct_weak_confidence_reinforces():
    decision = decide_next_action(_eval("correct", score=0.65), consecutive_struggles=0)
    assert decision.action == AdaptationAction.REINFORCE


def test_partially_correct_clarifies_gap():
    decision = decide_next_action(_eval("partially_correct", score=0.5), consecutive_struggles=0)
    assert decision.action == AdaptationAction.CLARIFY_GAP


def test_first_incorrect_answer_gets_new_analogy():
    decision = decide_next_action(
        _eval("incorrect", score=0.1, misconception="Thinks current increases with resistance"),
        consecutive_struggles=0,
    )
    assert decision.action == AdaptationAction.REEXPLAIN_NEW_ANALOGY
    assert decision.consecutive_struggles_after == 1


def test_repeated_incorrect_escalates_to_simpler_explanation():
    """The exact scenario from the demo script (spec section 3/29): student
    gets the Ohm's-law-style question wrong twice in a row -> must not repeat
    the same failed strategy."""
    decision = decide_next_action(_eval("incorrect", score=0.1), consecutive_struggles=1)
    assert decision.action == AdaptationAction.REEXPLAIN_SIMPLER
    assert decision.consecutive_struggles_after == 2


def test_uncertain_answer_asks_for_clarification_not_marked_wrong():
    decision = decide_next_action(_eval("uncertain", score=0.0), consecutive_struggles=0)
    assert decision.action == AdaptationAction.CLARIFY_GAP


def test_recovering_after_struggle_resets_streak():
    decision = decide_next_action(_eval("correct", score=0.9), consecutive_struggles=2)
    assert decision.action == AdaptationAction.ADVANCE_INCREASE_DIFFICULTY
    assert decision.consecutive_struggles_after == 0
