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


import uuid

def parse_inline_markdown(text: str) -> dict:
    """Parse text for markdown links and return Sanity children and markDefs."""
    children = []
    markDefs = []
    
    # Simple regex to find [text](url)
    pattern = re.compile(r'\[(.*?)\]\((.*?)\)')
    
    last_end = 0
    for match in pattern.finditer(text):
        start, end = match.span()
        # Add preceding text
        if start > last_end:
            children.append({"_type": "span", "text": text[last_end:start]})
            
        link_text = match.group(1)
        link_url = match.group(2)
        
        # Create markDef
        key = str(uuid.uuid4())[:12]
        markDefs.append({"_key": key, "_type": "link", "href": link_url})
        
        # Add link span
        children.append({"_type": "span", "marks": [key], "text": link_text})
        
        last_end = end
        
    # Add trailing text
    if last_end < len(text):
        children.append({"_type": "span", "text": text[last_end:]})
        
    if not children:
        children = [{"_type": "span", "text": text}]
        
    return {"children": children, "markDefs": markDefs}


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
            parsed = parse_inline_markdown(para)
            blocks.append({
                "_type": "block", "style": "normal",
                "children": parsed["children"],
                "markDefs": parsed["markDefs"]
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
