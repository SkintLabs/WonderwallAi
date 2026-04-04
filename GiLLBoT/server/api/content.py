"""
MeatHead — Content Generation & Draft Management API
Generates AI content, manages drafts, and provides improvement tools.
"""

import logging
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from server.db.engine import get_db
from server.db.models import ContentDraft
from server.services.ai_service import MeatHeadEngine

logger = logging.getLogger("meathead.api.content")

router = APIRouter()

# Singleton engine instance
_engine: Optional[MeatHeadEngine] = None


def get_engine() -> MeatHeadEngine:
    global _engine
    if _engine is None:
        _engine = MeatHeadEngine()
    return _engine


# --- Request schemas ---

class GenerateRequest(BaseModel):
    platform: str = Field(..., description="reddit | facebook | email | generic")
    product_context: str = Field(..., description="WonderwallAi | Jerry | Both")
    topic: str = Field(..., max_length=2000)
    tone: str = Field(default="casual", description="casual | professional | excited | educational")
    mention_count: int = Field(default=0, ge=0)


class ImproveRequest(BaseModel):
    original_text: str = Field(..., max_length=5000)
    instruction: str = Field(..., max_length=500)


class UpdateDraftRequest(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    status: Optional[str] = None


# --- Endpoints ---

@router.post("/generate")
async def generate_content(req: GenerateRequest):
    """Generate humanized marketing content for a platform."""
    engine = get_engine()
    if not engine.configured:
        raise HTTPException(status_code=503, detail="AI engine not configured (missing GROQ_API_KEY)")

    try:
        result = await engine.generate_content(
            platform=req.platform,
            product=req.product_context,
            topic=req.topic,
            tone=req.tone,
        )

        # Save as draft
        async with get_db() as db:
            draft = ContentDraft(
                user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),  # Internal tool, single user
                platform=req.platform,
                title=result.get("title"),
                body=result["body"],
                raw_body=result.get("raw_body"),
                metadata={
                    "product": req.product_context,
                    "topic": req.topic,
                    "tone": req.tone,
                    "mention_count": req.mention_count,
                },
                status="draft",
            )
            db.add(draft)
            await db.flush()
            draft_id = str(draft.id)

        return {
            "status": "success",
            "draft_id": draft_id,
            "draft": result["body"],
            "raw_draft": result.get("raw_body", result["body"]),
            "title": result.get("title"),
        }

    except Exception as e:
        logger.error(f"Content generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/improve")
async def improve_content(req: ImproveRequest):
    """Apply a specific editing instruction to existing text."""
    engine = get_engine()
    if not engine.configured:
        raise HTTPException(status_code=503, detail="AI engine not configured")

    try:
        improved = await engine.improve_draft(req.original_text, req.instruction)
        return {"status": "success", "draft": improved}
    except Exception as e:
        logger.error(f"Draft improvement failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/drafts")
async def list_drafts(status: Optional[str] = None, limit: int = 50):
    """List content drafts, optionally filtered by status."""
    async with get_db() as db:
        query = select(ContentDraft).order_by(ContentDraft.created_at.desc()).limit(limit)
        if status:
            query = query.where(ContentDraft.status == status)
        result = await db.execute(query)
        drafts = result.scalars().all()

    return {
        "drafts": [
            {
                "id": str(d.id),
                "platform": d.platform,
                "title": d.title,
                "body": d.body,
                "raw_body": d.raw_body,
                "status": d.status,
                "metadata": d.metadata,
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in drafts
        ]
    }


@router.get("/drafts/{draft_id}")
async def get_draft(draft_id: str):
    """Get a single draft by ID."""
    async with get_db() as db:
        result = await db.execute(
            select(ContentDraft).where(ContentDraft.id == uuid.UUID(draft_id))
        )
        draft = result.scalar_one_or_none()

    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    return {
        "id": str(draft.id),
        "platform": draft.platform,
        "title": draft.title,
        "body": draft.body,
        "raw_body": draft.raw_body,
        "status": draft.status,
        "metadata": draft.metadata,
        "created_at": draft.created_at.isoformat() if draft.created_at else None,
    }


@router.patch("/drafts/{draft_id}")
async def update_draft(draft_id: str, req: UpdateDraftRequest):
    """Update a draft's title, body, or status."""
    async with get_db() as db:
        result = await db.execute(
            select(ContentDraft).where(ContentDraft.id == uuid.UUID(draft_id))
        )
        draft = result.scalar_one_or_none()
        if not draft:
            raise HTTPException(status_code=404, detail="Draft not found")

        if req.title is not None:
            draft.title = req.title
        if req.body is not None:
            draft.body = req.body
        if req.status is not None:
            draft.status = req.status

    return {"status": "updated", "id": draft_id}


@router.delete("/drafts/{draft_id}")
async def delete_draft(draft_id: str):
    """Delete/discard a draft."""
    async with get_db() as db:
        result = await db.execute(
            select(ContentDraft).where(ContentDraft.id == uuid.UUID(draft_id))
        )
        draft = result.scalar_one_or_none()
        if not draft:
            raise HTTPException(status_code=404, detail="Draft not found")
        await db.delete(draft)

    return {"status": "deleted", "id": draft_id}
