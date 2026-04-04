"""
MeatHead — Social Media API
Reddit and Facebook posting, searching, and monitoring.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from server.db.engine import get_db
from server.db.models import SocialPost, ContentDraft

logger = logging.getLogger("meathead.api.social")

router = APIRouter()

# Service singletons (initialized on first use)
_reddit_service = None
_facebook_service = None


def get_reddit():
    global _reddit_service
    if _reddit_service is None:
        from server.services.reddit_service import RedditService
        _reddit_service = RedditService()
    return _reddit_service


def get_facebook():
    global _facebook_service
    if _facebook_service is None:
        from server.services.facebook_service import FacebookService
        _facebook_service = FacebookService()
    return _facebook_service


INTERNAL_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


# --- Reddit request schemas ---

class RedditPostRequest(BaseModel):
    subreddit: str = Field(..., max_length=100)
    title: str = Field(..., max_length=300)
    body: str = Field(..., max_length=10000)
    draft_id: Optional[str] = None


class RedditCommentRequest(BaseModel):
    post_id: str = Field(..., description="Reddit post ID (e.g. 'abc123')")
    body: str = Field(..., max_length=10000)
    draft_id: Optional[str] = None


class RedditSearchRequest(BaseModel):
    subreddit: str
    query: str
    limit: int = Field(default=10, le=25)


class FacebookPostRequest(BaseModel):
    message: str = Field(..., max_length=63206)
    link: Optional[str] = None
    draft_id: Optional[str] = None


# --- Reddit endpoints ---

@router.post("/reddit/post")
async def reddit_post(req: RedditPostRequest):
    """Submit a new text post to a subreddit."""
    reddit = get_reddit()
    if not reddit.configured:
        raise HTTPException(status_code=503, detail="Reddit not configured")

    try:
        result = await reddit.submit_post(req.subreddit, req.title, req.body)

        # Save to DB
        async with get_db() as db:
            post = SocialPost(
                user_id=INTERNAL_USER_ID,
                draft_id=uuid.UUID(req.draft_id) if req.draft_id else None,
                platform="reddit",
                platform_post_id=result["id"],
                post_url=result["url"],
                title=req.title,
                body=req.body,
                subreddit=req.subreddit,
                status="posted",
                posted_at=datetime.now(timezone.utc),
            )
            db.add(post)

            # Mark draft as posted if linked
            if req.draft_id:
                draft_result = await db.execute(
                    select(ContentDraft).where(ContentDraft.id == uuid.UUID(req.draft_id))
                )
                draft = draft_result.scalar_one_or_none()
                if draft:
                    draft.status = "posted"

        return {"status": "posted", "url": result["url"], "id": result["id"]}

    except Exception as e:
        logger.error(f"Reddit post failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reddit/comment")
async def reddit_comment(req: RedditCommentRequest):
    """Reply to a Reddit post."""
    reddit = get_reddit()
    if not reddit.configured:
        raise HTTPException(status_code=503, detail="Reddit not configured")

    try:
        result = await reddit.submit_comment(req.post_id, req.body)

        async with get_db() as db:
            post = SocialPost(
                user_id=INTERNAL_USER_ID,
                draft_id=uuid.UUID(req.draft_id) if req.draft_id else None,
                platform="reddit",
                platform_post_id=result["id"],
                post_url=result["url"],
                body=req.body,
                status="posted",
                posted_at=datetime.now(timezone.utc),
            )
            db.add(post)

            if req.draft_id:
                draft_result = await db.execute(
                    select(ContentDraft).where(ContentDraft.id == uuid.UUID(req.draft_id))
                )
                draft = draft_result.scalar_one_or_none()
                if draft:
                    draft.status = "posted"

        return {"status": "posted", "url": result["url"], "id": result["id"]}

    except Exception as e:
        logger.error(f"Reddit comment failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reddit/search")
async def reddit_search(subreddit: str, query: str, limit: int = 10):
    """Search a subreddit for relevant posts."""
    reddit = get_reddit()
    if not reddit.configured:
        raise HTTPException(status_code=503, detail="Reddit not configured")

    posts = await reddit.search_subreddit(subreddit, query, min(limit, 25))
    return {"posts": posts}


@router.get("/reddit/hot/{subreddit}")
async def reddit_hot(subreddit: str, limit: int = 10):
    """Get hot posts from a subreddit."""
    reddit = get_reddit()
    if not reddit.configured:
        raise HTTPException(status_code=503, detail="Reddit not configured")

    posts = await reddit.get_hot_posts(subreddit, min(limit, 25))
    return {"posts": posts}


@router.get("/reddit/inbox")
async def reddit_inbox():
    """Check Reddit inbox for replies."""
    reddit = get_reddit()
    if not reddit.configured:
        raise HTTPException(status_code=503, detail="Reddit not configured")

    messages = await reddit.get_inbox()
    return {"messages": messages}


# --- Facebook endpoints ---

@router.post("/facebook/post")
async def facebook_post(req: FacebookPostRequest):
    """Post to Facebook page."""
    fb = get_facebook()
    if not fb.configured:
        raise HTTPException(status_code=503, detail="Facebook not configured")

    try:
        result = await fb.post_to_page(req.message, req.link)

        async with get_db() as db:
            post = SocialPost(
                user_id=INTERNAL_USER_ID,
                draft_id=uuid.UUID(req.draft_id) if req.draft_id else None,
                platform="facebook",
                platform_post_id=result["post_id"],
                post_url=result["url"],
                body=req.message,
                status="posted",
                posted_at=datetime.now(timezone.utc),
            )
            db.add(post)

            if req.draft_id:
                draft_result = await db.execute(
                    select(ContentDraft).where(ContentDraft.id == uuid.UUID(req.draft_id))
                )
                draft = draft_result.scalar_one_or_none()
                if draft:
                    draft.status = "posted"

        return {"status": "posted", "post_id": result["post_id"], "url": result["url"]}

    except Exception as e:
        logger.error(f"Facebook post failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/facebook/posts")
async def facebook_posts(limit: int = 10):
    """Get recent Facebook page posts with engagement."""
    fb = get_facebook()
    if not fb.configured:
        raise HTTPException(status_code=503, detail="Facebook not configured")

    posts = await fb.get_page_posts(min(limit, 25))
    return {"posts": posts}


# --- Cross-platform ---

@router.get("/posts")
async def all_posts(limit: int = 50, platform: Optional[str] = None):
    """Get all published posts across platforms."""
    async with get_db() as db:
        query = select(SocialPost).order_by(SocialPost.created_at.desc()).limit(limit)
        if platform:
            query = query.where(SocialPost.platform == platform)
        result = await db.execute(query)
        posts = result.scalars().all()

    return {
        "posts": [
            {
                "id": str(p.id),
                "platform": p.platform,
                "title": p.title,
                "body": p.body[:200] + ("..." if len(p.body) > 200 else ""),
                "subreddit": p.subreddit,
                "url": p.post_url,
                "status": p.status,
                "likes": p.likes,
                "comments": p.comments,
                "shares": p.shares,
                "posted_at": p.posted_at.isoformat() if p.posted_at else None,
            }
            for p in posts
        ]
    }
