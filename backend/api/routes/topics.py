from fastapi import APIRouter, Depends, HTTPException

from backend.core.security import get_current_user
from backend import models
from backend.schemas.schemas import TopicAnalyzeIn
from backend.services.llm.factory import get_llm_provider
from backend.prompts.analysis import TOPIC_ANALYZER_SYSTEM, build_topic_analysis_prompt

router = APIRouter(prefix="/api/topics", tags=["topics"])


@router.post("/analyze")
async def analyze_topic(payload: TopicAnalyzeIn, user: models.User = Depends(get_current_user)):
    llm = get_llm_provider()
    try:
        return await llm.complete_json(
            TOPIC_ANALYZER_SYSTEM, build_topic_analysis_prompt(payload.topic), max_tokens=250, temperature=0.2
        )
    except Exception as e:
        raise HTTPException(502, f"Topic analysis failed: {e}") from e
