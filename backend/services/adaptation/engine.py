"""
ADAPTIVE TEACHING ENGINE (spec section 10).

This is deliberately a small, pure, fully unit-testable decision function —
NOT buried inside a prompt, and NOT a chain of ad-hoc if/else scattered
through the API layer. The LLM handles diagnosis (evaluation.evaluator);
this module owns the *policy* of what to do about it, so the policy can be
audited, tested, and improved independently of any LLM call.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

from backend.services.evaluation.evaluator import EvaluationResult


class AdaptationAction(str, Enum):
    ADVANCE_INCREASE_DIFFICULTY = "advance_increase_difficulty"
    ADVANCE = "advance"
    REINFORCE = "reinforce"
    CLARIFY_GAP = "clarify_gap"
    REEXPLAIN_NEW_ANALOGY = "reexplain_new_analogy"
    REEXPLAIN_SIMPLER = "reexplain_simpler"


@dataclass
class AdaptationDecision:
    action: AdaptationAction
    reason: str
    consecutive_struggles_after: int


# A "strong" correct answer is high score with no detected misconception.
STRONG_CONFIDENCE_THRESHOLD = 0.85
WEAK_CONFIDENCE_THRESHOLD = 0.6
ESCALATE_AFTER_STRUGGLES = 2  # after this many consecutive incorrect on same concept, simplify further


def decide_next_action(
    evaluation: EvaluationResult,
    *,
    consecutive_struggles: int,
) -> AdaptationDecision:
    """
    Pure decision function per spec section 10's tree:

        Correct + strong confidence  -> increase difficulty / continue
        Correct + weak confidence    -> reinforce concept
        Partially correct            -> clarify missing part
        Incorrect                    -> re-explain (new analogy first,
                                         simpler explanation if it recurs)

    `consecutive_struggles` lets the caller escalate: the first incorrect
    answer on a concept gets a new-analogy re-explanation; if the student is
    STILL wrong after that, we switch strategy to a simpler explanation
    rather than repeating the same failed approach.
    """
    cls = evaluation.classification

    if cls == "correct":
        if evaluation.score >= STRONG_CONFIDENCE_THRESHOLD:
            return AdaptationDecision(
                AdaptationAction.ADVANCE_INCREASE_DIFFICULTY,
                "Correct with strong confidence — ready for more challenge.",
                0,
            )
        return AdaptationDecision(
            AdaptationAction.REINFORCE,
            "Correct but confidence is weak — reinforce before moving on.",
            0,
        )

    if cls == "partially_correct":
        return AdaptationDecision(
            AdaptationAction.CLARIFY_GAP,
            "Partially correct — clarify the specific missing piece rather than re-teaching everything.",
            consecutive_struggles,
        )

    if cls == "incorrect":
        next_struggles = consecutive_struggles + 1
        if next_struggles >= ESCALATE_AFTER_STRUGGLES:
            return AdaptationDecision(
                AdaptationAction.REEXPLAIN_SIMPLER,
                f"Incorrect for the {next_struggles}th time on this concept — "
                f"switch to a simpler explanation strategy rather than repeating what didn't work.",
                next_struggles,
            )
        return AdaptationDecision(
            AdaptationAction.REEXPLAIN_NEW_ANALOGY,
            "Incorrect — re-explain the concept with a new analogy and example, then re-check.",
            next_struggles,
        )

    # uncertain / unparseable answer
    return AdaptationDecision(
        AdaptationAction.CLARIFY_GAP,
        "Answer was unclear — ask a clarifying follow-up before judging correctness.",
        consecutive_struggles,
    )
