"""
MeatHead — Facebook Service
Posts to a Facebook Page and fetches engagement data via the Graph API.
Uses a never-expiring Page Access Token (generated via Graph API Explorer).
"""

import logging
from typing import Optional

import httpx

logger = logging.getLogger("meathead.facebook")


class FacebookService:
    """Facebook Graph API wrapper for page posting and engagement tracking."""

    def __init__(self):
        from server.config import get_settings
        settings = get_settings()

        self.page_id = settings.facebook_page_id
        self.access_token = settings.facebook_access_token
        self.configured = settings.facebook_configured
        self.api_version = "v19.0"
        self.base_url = f"https://graph.facebook.com/{self.api_version}"

        if self.configured:
            logger.info(f"FacebookService initialized (page: {self.page_id})")
        else:
            logger.warning("FacebookService: credentials not set. Facebook features disabled.")

    async def post_to_page(self, message: str, link: Optional[str] = None) -> dict:
        """Publish a post to the Facebook Page."""
        if not self.configured:
            raise RuntimeError("Facebook not configured")

        url = f"{self.base_url}/{self.page_id}/feed"
        payload = {
            "message": message,
            "access_token": self.access_token,
        }
        if link:
            payload["link"] = link

        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=payload, timeout=30.0)

            if response.status_code == 200:
                data = response.json()
                post_id = data.get("id", "")
                logger.info(f"Posted to Facebook page. ID: {post_id}")
                return {
                    "post_id": post_id,
                    "url": f"https://facebook.com/{post_id}",
                }
            else:
                error_data = response.json()
                error_msg = error_data.get("error", {}).get("message", "Unknown error")
                logger.error(f"Facebook API error: {error_msg}")
                raise RuntimeError(f"Facebook API error: {error_msg}")

    async def get_page_posts(self, limit: int = 10) -> list[dict]:
        """Fetch recent page posts with engagement stats."""
        if not self.configured:
            return []

        url = f"{self.base_url}/{self.page_id}/posts"
        params = {
            "fields": "id,message,created_time,permalink_url,shares,comments.summary(total_count),reactions.summary(total_count)",
            "limit": limit,
            "access_token": self.access_token,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=30.0)

            if response.status_code != 200:
                logger.error(f"Failed to fetch Facebook posts: {response.text[:200]}")
                return []

            data = response.json().get("data", [])
            posts = []
            for post in data:
                shares = post.get("shares", {}).get("count", 0)
                comments = post.get("comments", {}).get("summary", {}).get("total_count", 0)
                reactions = post.get("reactions", {}).get("summary", {}).get("total_count", 0)

                posts.append({
                    "id": post.get("id"),
                    "message": post.get("message", ""),
                    "created_at": post.get("created_time"),
                    "url": post.get("permalink_url", f"https://facebook.com/{post.get('id')}"),
                    "likes": reactions,
                    "comments": comments,
                    "shares": shares,
                })

            return posts
