"""
sanity_sync.py — Sync blog posts from Supabase to Sanity CMS.
Converts markdown content to Sanity's Portable Text format and
uses the Sanity Mutations API to create documents.
"""

import re
import logging
from typing import List, Optional
from datetime import datetime, timezone

import httpx

from config import SiteConfig

logger = logging.getLogger(__name__)


def markdown_to_portable_text(markdown: str) -> list:
    """Convert markdown to Sanity Portable Text blocks."""
    blocks = []
    paragraphs = markdown.split('\n\n')

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if para.startswith('## '):
            blocks.append({
                "_type": "block", "style": "h2",
                "children": [{"_type": "span", "text": para[3:].strip()}],
            })
        elif para.startswith('### '):
            blocks.append({
                "_type": "block", "style": "h3",
                "children": [{"_type": "span", "text": para[4:].strip()}],
            })
        else:
            blocks.append({
                "_type": "block", "style": "normal",
                "children": [{"_type": "span", "text": para}],
            })
    return blocks


async def sync_to_sanity(
    site: SiteConfig, title: str, slug: str, content: str,
    keywords: List[str], meta_description: str,
) -> Optional[str]:
    """Create or update a blog post in Sanity via Mutations API."""
    api_url = (
        f"https://{site.sanity_project_id}.api.sanity.io"
        f"/v2024-01-01/data/mutate/{site.sanity_dataset}"
    )
    doc_id = f"post-{slug}"
    doc = {
        "_id": doc_id, "_type": "post",
        "title": title,
        "slug": {"_type": "slug", "current": slug},
        "body": markdown_to_portable_text(content),
        "seoKeywords": keywords,
        "metaDescription": meta_description,
        "publishedAt": datetime.now(timezone.utc).isoformat(),
        "author": "AI Writer",
    }
    mutations = {"mutations": [{"createOrReplace": doc}]}
    headers = {
        "Authorization": f"Bearer {site.sanity_token}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.post(api_url, json=mutations, headers=headers)
            resp.raise_for_status()
            logger.info(f"[{site.name}] Synced to Sanity: '{title}'")
            return doc_id
        except Exception as e:
            logger.error(f"[{site.name}] Sanity sync failed: {e}")
            return None
