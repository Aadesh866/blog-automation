"""
scheduler.py — Automated blog generation scheduler.
Runs every 2 hours, round-robins across configured sites,
generates 2-5 posts per cycle to hit 10-30 posts/day target.
"""

import asyncio
import logging
import random
import sys
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from config import get_settings, get_sites
from generator import generate_blog_post
from post_processor import process_post
from link_injector import inject_links
from embeddings import generate_post_embedding
from supabase_client import insert_post
from sanity_sync import sync_to_sanity

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("scheduler")

settings = get_settings()


async def generate_for_site(site):
    """Generate a batch of posts for a single site."""
    posts_to_generate = site.posts_per_cycle
    logger.info(f"=== Generating {posts_to_generate} posts for [{site.name}] ===")

    for i in range(posts_to_generate):
        try:
            # Pick a random topic and subset of keywords
            topic = random.choice(site.topics) if site.topics else "technology trends"
            keywords = random.sample(
                site.keywords,
                min(4, len(site.keywords))
            ) if site.keywords else ["technology"]

            logger.info(f"[{site.name}] Post {i+1}/{posts_to_generate}: topic='{topic}'")

            # Step 1: Generate raw blog post via LLM
            post = await generate_blog_post(
                topic=topic,
                keywords=keywords,
                target_word_count=settings.target_word_count,
            )

            # Step 2: Post-process for anti-AI detection
            processed_content, quality_score = process_post(post["content"])

            # Step 3: Inject internal/external links
            final_content = inject_links(
                content=processed_content,
                internal_links=site.internal_links,
                external_links=site.external_links,
                site_domain=site.domain,
            )

            # Step 4: Generate embedding for semantic search
            embedding = await generate_post_embedding(
                title=post["title"],
                content=final_content,
                keywords=keywords,
            )

            # Step 5: Insert into Supabase
            result = await insert_post(
                site=site,
                title=post["title"],
                slug=post["slug"],
                content=final_content,
                keywords=keywords,
                meta_description=post["meta_description"],
                word_count=post["word_count"],
                quality_score=quality_score,
                embedding=embedding if embedding else None,
            )

            # Step 6: Sync to Sanity CMS
            await sync_to_sanity(
                site=site,
                title=post["title"],
                slug=post["slug"],
                content=final_content,
                keywords=keywords,
                meta_description=post["meta_description"],
            )

            logger.info(
                f"[{site.name}] ✓ Post {i+1} complete: '{post['title']}' "
                f"({post['word_count']} words, quality: {quality_score}/100)"
            )

        except Exception as e:
            logger.error(f"[{site.name}] ✗ Post {i+1} failed: {e}", exc_info=True)
            continue


async def run_generation_cycle():
    """Run one full generation cycle across all configured sites."""
    logger.info(f"{'='*60}")
    logger.info(f"Generation cycle started at {datetime.utcnow().isoformat()}")
    logger.info(f"{'='*60}")

    sites = get_sites()
    for site in sites:
        await generate_for_site(site)

    logger.info(f"Generation cycle complete.")


async def main():
    """Start the scheduler."""
    logger.info("Blog automation scheduler starting...")
    logger.info(f"Schedule: every {settings.schedule_interval_hours} hours")
    logger.info(f"Sites configured: {len(get_sites())}")
    for site in get_sites():
        logger.info(f"  - {site.name}: {site.posts_per_cycle} posts/cycle")

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        run_generation_cycle,
        trigger=IntervalTrigger(hours=settings.schedule_interval_hours),
        id="blog_generation",
        name="Blog Generation Cycle",
        next_run_time=datetime.now(),  # Run immediately on start
    )
    scheduler.start()

    # Keep the event loop running
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler shutting down...")
        scheduler.shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Exiting...")
