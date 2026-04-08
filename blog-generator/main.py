"""
main.py — FastAPI application for the blog generation API.
Provides endpoints for on-demand generation, batch generation,
distribution, and status monitoring.
"""

import logging
import sys
from typing import List, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel

from config import get_settings, get_sites, get_site_by_id
from generator import generate_blog_post
from post_processor import process_post
from link_injector import inject_links
from embeddings import generate_post_embedding
from supabase_client import insert_post, get_stats, get_recent_posts
from sanity_sync import sync_to_sanity

# ── Logging setup ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("blog-api")
settings = get_settings()

# ── FastAPI app ──
app = FastAPI(
    title="Blog Automation API",
    description="Generate SEO-optimised blog posts via LLM and distribute to multiple websites",
    version="1.0.0",
)


# ── Request/Response models ──

class GenerateRequest(BaseModel):
    site_id: str
    topic: str
    keywords: List[str] = []
    target_word_count: int = 1200

class GenerateResponse(BaseModel):
    title: str
    slug: str
    content: str
    meta_description: str
    keywords: List[str]
    word_count: int
    quality_score: float

class BatchRequest(BaseModel):
    site_id: str
    topics: List[str]
    keywords: List[str] = []
    target_word_count: int = 1200

class SiteInfo(BaseModel):
    id: str
    name: str
    domain: str
    posts_per_cycle: int
    topic_count: int
    keyword_count: int


# ── Health check ──

@app.get("/health")
async def health():
    return {"status": "healthy", "llm_url": settings.llm_api_url}


# ── List configured sites ──

@app.get("/sites", response_model=List[SiteInfo])
async def list_sites():
    sites = get_sites()
    return [
        SiteInfo(
            id=s.id, name=s.name, domain=s.domain,
            posts_per_cycle=s.posts_per_cycle,
            topic_count=len(s.topics), keyword_count=len(s.keywords),
        )
        for s in sites
    ]


# ── Generate a single blog post ──

@app.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    """Generate a single blog post and distribute to the site's Supabase + Sanity."""
    try:
        site = get_site_by_id(req.site_id)
    except ValueError:
        raise HTTPException(404, f"Site '{req.site_id}' not found")

    keywords = req.keywords if req.keywords else site.keywords[:4]

    # Step 1: Generate via LLM
    logger.info(f"Generating post for [{site.name}]: topic='{req.topic}'")
    post = await generate_blog_post(
        topic=req.topic, keywords=keywords,
        target_word_count=req.target_word_count,
    )

    # Step 2: Post-process
    processed_content, quality_score = process_post(post["content"])

    # Step 3: Inject links
    final_content = inject_links(
        content=processed_content,
        internal_links=site.internal_links,
        external_links=site.external_links,
        site_domain=site.domain,
    )

    # Step 4: Generate embedding
    embedding = await generate_post_embedding(
        title=post["title"], content=final_content, keywords=keywords,
    )

    # Step 5: Insert into Supabase
    await insert_post(
        site=site, title=post["title"], slug=post["slug"],
        content=final_content, keywords=keywords,
        meta_description=post["meta_description"],
        word_count=post["word_count"], quality_score=quality_score,
        embedding=embedding if embedding else None,
    )

    # Step 6: Sync to Sanity
    await sync_to_sanity(
        site=site, title=post["title"], slug=post["slug"],
        content=final_content, keywords=keywords,
        meta_description=post["meta_description"],
    )

    return GenerateResponse(
        title=post["title"], slug=post["slug"],
        content=final_content, meta_description=post["meta_description"],
        keywords=keywords, word_count=post["word_count"],
        quality_score=quality_score,
    )


# ── Batch generate (runs in background) ──

@app.post("/generate/batch")
async def generate_batch(req: BatchRequest, background_tasks: BackgroundTasks):
    """Queue batch generation for multiple topics. Returns immediately."""
    try:
        site = get_site_by_id(req.site_id)
    except ValueError:
        raise HTTPException(404, f"Site '{req.site_id}' not found")

    async def _batch():
        for topic in req.topics:
            try:
                post = await generate_blog_post(
                    topic=topic, keywords=req.keywords or site.keywords[:4],
                    target_word_count=req.target_word_count,
                )
                processed, quality = process_post(post["content"])
                final = inject_links(processed, site.internal_links, site.external_links, site.domain)
                emb = await generate_post_embedding(post["title"], final, req.keywords or site.keywords[:4])
                await insert_post(
                    site, post["title"], post["slug"], final,
                    req.keywords or site.keywords[:4], post["meta_description"],
                    post["word_count"], quality, emb if emb else None,
                )
                await sync_to_sanity(
                    site, post["title"], post["slug"], final,
                    req.keywords or site.keywords[:4], post["meta_description"],
                )
                logger.info(f"Batch: generated '{post['title']}'")
            except Exception as e:
                logger.error(f"Batch: failed for topic '{topic}': {e}")

    background_tasks.add_task(_batch)
    return {
        "message": f"Batch generation queued for {len(req.topics)} topics",
        "site": site.name,
    }


# ── Per-site stats ──

@app.get("/status/{site_id}")
async def site_status(site_id: str):
    """Get generation stats for a specific site."""
    try:
        site = get_site_by_id(site_id)
    except ValueError:
        raise HTTPException(404, f"Site '{site_id}' not found")

    stats = await get_stats(site)
    recent = await get_recent_posts(site, limit=5)

    return {
        "site": site.name,
        "stats": stats,
        "recent_posts": recent,
    }


# ── Global status ──

@app.get("/status")
async def global_status():
    """Get generation stats across all sites."""
    sites = get_sites()
    results = []
    for site in sites:
        stats = await get_stats(site)
        results.append({"site_id": site.id, "name": site.name, "stats": stats})
    return {"sites": results}
