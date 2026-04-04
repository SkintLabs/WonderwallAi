"""
MeatHead — Reddit Service
Async Reddit integration using asyncpraw for searching, posting, and inbox monitoring.
"""

import logging
from typing import Optional

logger = logging.getLogger("meathead.reddit")


class RedditService:
    """Async Reddit API wrapper using asyncpraw."""

    def __init__(self):
        from server.config import get_settings
        settings = get_settings()

        self.configured = settings.reddit_configured
        self._reddit = None

        if self.configured:
            try:
                import asyncpraw
                self._reddit = asyncpraw.Reddit(
                    client_id=settings.reddit_client_id,
                    client_secret=settings.reddit_client_secret,
                    username=settings.reddit_username,
                    password=settings.reddit_password,
                    user_agent=f"script:skintlabs.meathead:v1.0 (by u/{settings.reddit_username})",
                )
                logger.info(f"RedditService initialized (user: {settings.reddit_username})")
            except ImportError:
                logger.warning("asyncpraw not installed. Reddit features disabled.")
                self.configured = False
        else:
            logger.warning("RedditService: credentials not set. Reddit features disabled.")

    async def search_subreddit(self, subreddit_name: str, query: str, limit: int = 10) -> list[dict]:
        """Search a subreddit for targeted keywords."""
        if not self._reddit:
            return []

        subreddit = await self._reddit.subreddit(subreddit_name)
        posts = []
        async for submission in subreddit.search(query, sort="new", limit=limit):
            posts.append({
                "id": submission.id,
                "title": submission.title,
                "url": f"https://reddit.com{submission.permalink}",
                "body": (submission.selftext or "")[:500],
                "score": submission.score,
                "num_comments": submission.num_comments,
                "author": str(submission.author) if submission.author else "[deleted]",
                "created_utc": submission.created_utc,
            })
        return posts

    async def get_hot_posts(self, subreddit_name: str, limit: int = 10) -> list[dict]:
        """Get hot posts for discovery."""
        if not self._reddit:
            return []

        subreddit = await self._reddit.subreddit(subreddit_name)
        posts = []
        async for submission in subreddit.hot(limit=limit):
            posts.append({
                "id": submission.id,
                "title": submission.title,
                "url": f"https://reddit.com{submission.permalink}",
                "body": (submission.selftext or "")[:500],
                "score": submission.score,
                "num_comments": submission.num_comments,
                "author": str(submission.author) if submission.author else "[deleted]",
                "created_utc": submission.created_utc,
            })
        return posts

    async def get_inbox(self, limit: int = 10) -> list[dict]:
        """Check for unread replies and messages."""
        if not self._reddit:
            return []

        messages = []
        async for item in self._reddit.inbox.unread(limit=limit):
            messages.append({
                "id": item.id,
                "author": str(item.author) if item.author else "[deleted]",
                "body": item.body,
                "type": "comment_reply" if item.was_comment else "direct_message",
                "subject": getattr(item, "subject", None),
                "created_utc": item.created_utc,
            })
        return messages

    async def submit_post(self, subreddit_name: str, title: str, body: str) -> dict:
        """Submit a new text post to a subreddit."""
        if not self._reddit:
            raise RuntimeError("Reddit not configured")

        try:
            subreddit = await self._reddit.subreddit(subreddit_name)
            submission = await subreddit.submit(title, selftext=body)
            permalink = f"https://reddit.com{submission.permalink}"
            logger.info(f"Posted to r/{subreddit_name}: {permalink}")
            return {"id": submission.id, "url": permalink}
        except Exception as e:
            logger.error(f"Failed to post to r/{subreddit_name}: {e}")
            raise

    async def submit_comment(self, post_id: str, body: str) -> dict:
        """Reply to a specific Reddit post."""
        if not self._reddit:
            raise RuntimeError("Reddit not configured")

        try:
            submission = await self._reddit.submission(id=post_id)
            comment = await submission.reply(body)
            permalink = f"https://reddit.com{comment.permalink}"
            logger.info(f"Commented on {post_id}: {permalink}")
            return {"id": comment.id, "url": permalink}
        except Exception as e:
            logger.error(f"Failed to comment on {post_id}: {e}")
            raise

    async def close(self):
        """Shutdown cleanup — close the aiohttp session."""
        if self._reddit:
            await self._reddit.close()
