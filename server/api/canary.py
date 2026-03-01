"""Canary token endpoints."""

from fastapi import APIRouter, Depends, Query

from server.auth import get_current_api_key
from server.db.models import ApiKey
from server.helpers import get_wonderwall_for_key
from server.rate_limiter import check_rate_limit
from server.schemas.requests import CanaryGenerateRequest
from server.schemas.responses import CanaryResponse

router = APIRouter(prefix="/v1/canary", tags=["Canary"])


@router.post("/generate", response_model=CanaryResponse)
async def generate_canary(
    req: CanaryGenerateRequest,
    api_key: ApiKey = Depends(get_current_api_key),
):
    """Generate a canary token and the prompt block to inject into your LLM."""
    check_rate_limit(api_key.id, api_key.rate_limit)

    instance = await get_wonderwall_for_key(api_key)
    token = instance.generate_canary(req.session_id)
    prompt_block = instance.get_canary_prompt(token)

    return CanaryResponse(canary_token=token, prompt_block=prompt_block)


@router.get("/prompt")
async def get_canary_prompt(
    canary_token: str = Query(..., min_length=1),
    api_key: ApiKey = Depends(get_current_api_key),
):
    """Get the prompt block for an existing canary token."""
    instance = await get_wonderwall_for_key(api_key)
    return {"prompt_block": instance.get_canary_prompt(canary_token)}
