"""
supabase_client.py — Multi-site Supabase client for inserting and querying blog posts.
Each site has its own Supabase project with separate credentials.
"""

import logging
from typing import Dict, List, Optional

from supabase import create_client, Client

from config import SiteConfig

logger = logging.getLogger(__name__)

# Cache clients to avoid recreating them
_clients: Dict[str, Client] = {}


def get_client(site: SiteConfig) -> Client:
    """Get or create a Supabase client for the given site (using service role key)."""
    if site.id not in _clients:
        _clients[site.id] = create_client(
            site.supabase_url,
            site.supabase_service_key,  # Service role for full access (bypasses RLS)
        )
    return _clients[site.id]


async def insert_post(
    site: SiteConfig,
    title: str,
    slug: str,
    content: str,
    keywords: List[str],
    meta_description: str,
    word_count: int,
    quality_score: float,
    embedding: Optional[List[float]] = None,
) -> dict:
    """
    Insert a generated blog post into the site's Supabase posts table.

    Args:
        site: Site configuration with Supabase credentials
        title, slug, content, etc.: Post data
        embedding: Optional 768-dim vector for semantic search

    Returns:
        The inserted row data
    """
    client = get_client(site)

    reading_time = max(1, word_count // 200)  # ~200 wpm reading speed

    post_data = {
        "title": title,
        "slug": slug,
        "content": content,
        "keywords": keywords,
        "meta_description": meta_description,
        "status": "published",  # Auto-publish (change to 'draft' if you want manual review)
        "word_count": word_count,
        "reading_time": reading_time,
        "quality_score": quality_score,
    }

    # Add embedding if available
    if embedding and len(embedding) > 0:
        post_data["embedding"] = embedding

    try:
        result = client.table("posts").insert(post_data).execute()

        if result.data:
            logger.info(f"[{site.name}] Post inserted: '{title}' (slug: {slug})")
            return result.data[0]
        else:
            logger.error(f"[{site.name}] Insert returned no data for: {title}")
            return {}

    except Exception as e:
        # Handle duplicate slug by appending a suffix
        if "duplicate key" in str(e).lower() or "unique" in str(e).lower():
            logger.warning(f"[{site.name}] Duplicate slug '{slug}', appending suffix...")
            import time
            post_data["slug"] = f"{slug}-{int(time.time()) % 10000}"
            result = client.table("posts").insert(post_data).execute()
            return result.data[0] if result.data else {}
        else:
            logger.error(f"[{site.name}] Failed to insert post: {e}")
            raise


async def get_post_count(site: SiteConfig) -> int:
    """Get total post count for a site."""
    client = get_client(site)
    try:
        result = client.table("posts").select("id", count="exact").execute()
        return result.count or 0
    except Exception as e:
        logger.error(f"[{site.name}] Failed to get post count: {e}")
        return 0


async def get_recent_posts(site: SiteConfig, limit: int = 10) -> list:
    """Get recent posts for a site."""
    client = get_client(site)
    try:
        result = (
            client.table("posts")
            .select("id,title,slug,created_at,status,quality_score,word_count")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []
    except Exception as e:
        logger.error(f"[{site.name}] Failed to get recent posts: {e}")
        return []


async def get_stats(site: SiteConfig) -> dict:
    """Get post statistics for the admin dashboard."""
    client = get_client(site)
    try:
        result = client.rpc("", {}).execute()  # Use the post_stats view instead
        # Fallback: query directly
        all_posts = client.table("posts").select("id,status,quality_score,word_count,created_at").execute()
        posts = all_posts.data or []

        from datetime import datetime, timedelta, timezone
        now = datetime.now(timezone.utc)
        day_ago = now - timedelta(days=1)
        week_ago = now - timedelta(days=7)

        total = len(posts)
        published = sum(1 for p in posts if p.get("status") == "published")
        drafts = sum(1 for p in posts if p.get("status") == "draft")
        today = sum(1 for p in posts if p.get("created_at", "") > day_ago.isoformat())
        this_week = sum(1 for p in posts if p.get("created_at", "") > week_ago.isoformat())
        avg_quality = sum(p.get("quality_score", 0) for p in posts) / max(1, total)
        avg_words = sum(p.get("word_count", 0) for p in posts) / max(1, total)

        return {
            "total_posts": total,
            "published_posts": published,
            "draft_posts": drafts,
            "posts_today": today,
            "posts_this_week": this_week,
            "avg_quality_score": round(avg_quality, 1),
            "avg_word_count": round(avg_words),
        }
    except Exception as e:
        logger.error(f"[{site.name}] Failed to get stats: {e}")
        return {}
