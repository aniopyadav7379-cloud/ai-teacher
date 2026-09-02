"""Subject-aware visual planning (spec section 13). Produces a spec the
frontend's visual renderer (diagram/equation/graph/code/timeline components)
consumes — never a random stock image."""
from __future__ import annotations
from backend.services.llm.factory import get_llm_provider
from backend.prompts.teaching import VISUAL_PLANNER_SYSTEM, build_visual_prompt


async def plan_visual(*, subject: str, concept: str, explanation: str) -> dict:
    llm = get_llm_provider()
    prompt = build_visual_prompt(subject=subject, concept=concept, explanation=explanation)
    return await llm.complete_json(VISUAL_PLANNER_SYSTEM, prompt, max_tokens=500, temperature=0.3)
