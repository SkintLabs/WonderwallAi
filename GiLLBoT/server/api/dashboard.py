"""
MeatHead — Dashboard API
Aggregated stats across all content, social posts, and emails.
"""

import logging

from fastapi import APIRouter, HTTPException
from sqlalchemy import select, func

from server.db.engine import get_db
from server.db.models import ContentDraft, SocialPost, SequenceExecution

logger = logging.getLogger("meathead.dashboard")

router = APIRouter()


@router.get("/stats")
async def get_dashboard_stats():
    """Aggregated MeatHead activity stats for the overview tab."""
    try:
        async with get_db() as db:
            drafts = (await db.execute(
                select(func.count(ContentDraft.id))
            )).scalar() or 0

            published = (await db.execute(
                select(func.count(SocialPost.id)).where(SocialPost.status == "posted")
            )).scalar() or 0

            engagement_result = await db.execute(
                select(func.coalesce(
                    func.sum(SocialPost.likes + SocialPost.comments + SocialPost.shares), 0
                ))
            )
            total_engagement = engagement_result.scalar() or 0

            emails_sent = (await db.execute(
                select(func.count(SequenceExecution.id)).where(
                    SequenceExecution.status.in_(["sent", "opened", "clicked", "replied"])
                )
            )).scalar() or 0

        # Service status
        from server.config import get_settings
        settings = get_settings()

        return {
            "status": "active",
            "totals": {
                "drafts": drafts,
                "published": published,
                "engagement": total_engagement,
                "emails_sent": emails_sent,
            },
            "services": {
                "groq": settings.groq_configured,
                "reddit": settings.reddit_configured,
                "facebook": settings.facebook_configured,
                "sendgrid": settings.sendgrid_configured,
            },
        }

    except Exception as e:
        logger.error(f"Dashboard stats failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load stats")
