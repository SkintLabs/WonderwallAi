"""
MeatHead / GiLLBoT — Campaigns API
CRUD for email outreach campaigns.
"""

import logging
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from server.db.engine import get_db
from server.db.models import Campaign, SequenceStep

logger = logging.getLogger("meathead.campaigns")

router = APIRouter()

INTERNAL_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


class CampaignCreate(BaseModel):
    name: str = Field(..., max_length=255)
    from_name: str = Field(..., max_length=255)
    from_email: str = Field(..., max_length=255)
    reply_to_email: Optional[str] = None
    context_prompt: Optional[str] = None


class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    from_name: Optional[str] = None
    from_email: Optional[str] = None
    context_prompt: Optional[str] = None


@router.get("")
async def list_campaigns():
    """List all campaigns."""
    async with get_db() as db:
        result = await db.execute(
            select(Campaign).order_by(Campaign.created_at.desc()).limit(50)
        )
        campaigns = result.scalars().all()

    return {
        "campaigns": [
            {
                "id": str(c.id),
                "name": c.name,
                "status": c.status,
                "from_name": c.from_name,
                "from_email": c.from_email,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in campaigns
        ]
    }


@router.post("")
async def create_campaign(req: CampaignCreate):
    """Create a new email campaign."""
    async with get_db() as db:
        campaign = Campaign(
            user_id=INTERNAL_USER_ID,
            name=req.name,
            from_name=req.from_name,
            from_email=req.from_email,
            reply_to_email=req.reply_to_email,
            context_prompt=req.context_prompt,
            status="draft",
        )
        db.add(campaign)
        await db.flush()
        campaign_id = str(campaign.id)

    return {"status": "created", "id": campaign_id}


@router.get("/{campaign_id}")
async def get_campaign(campaign_id: str):
    """Get campaign details."""
    async with get_db() as db:
        result = await db.execute(
            select(Campaign).where(Campaign.id == uuid.UUID(campaign_id))
        )
        campaign = result.scalar_one_or_none()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    return {
        "id": str(campaign.id),
        "name": campaign.name,
        "status": campaign.status,
        "from_name": campaign.from_name,
        "from_email": campaign.from_email,
        "reply_to_email": campaign.reply_to_email,
        "context_prompt": campaign.context_prompt,
        "created_at": campaign.created_at.isoformat() if campaign.created_at else None,
    }


@router.patch("/{campaign_id}")
async def update_campaign(campaign_id: str, req: CampaignUpdate):
    """Update a campaign."""
    async with get_db() as db:
        result = await db.execute(
            select(Campaign).where(Campaign.id == uuid.UUID(campaign_id))
        )
        campaign = result.scalar_one_or_none()
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        if req.name is not None:
            campaign.name = req.name
        if req.status is not None:
            campaign.status = req.status
        if req.from_name is not None:
            campaign.from_name = req.from_name
        if req.from_email is not None:
            campaign.from_email = req.from_email
        if req.context_prompt is not None:
            campaign.context_prompt = req.context_prompt

    return {"status": "updated", "id": campaign_id}
