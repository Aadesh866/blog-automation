"""
generator.py — Core blog generation pipeline.
Calls the remote Ollama LLM API to generate structured, SEO-optimised blog posts.

Pipeline:
1. Generate outline (title + sections) from topic/keywords
2. Write introduction
3. Expand each section into full prose (~300 words each)
4. Write conclusion
5. Assemble final markdown document
"""

import json
import logging
import re
from typing import List, Optional

import httpx
from slugify import slugify

from config import get_settings
from prompts import (
    SYSTEM_PROMPT,
    OUTLINE_PROMPT,
    SECTION_PROMPT,
    INTRO_PROMPT,
    CONCLUSION_PROMPT,
)

logger = logging.getLogger(__name__)
settings = get_settings()


async def call_llm(prompt: str, system: str = SYSTEM_PROMPT, temperature: float = 0.8) -> str:
    """
    Call the LLM API and return the generated text.
    Supports multiple providers:
    - groq/mistral/openai: Uses OpenAI-compatible /v1/chat/completions
    - ollama: Uses Ollama's native /api/generate
    """
    provider = settings.llm_provider.lower()

    if provider in ("groq", "mistral", "openai"):
        return await _call_openai_compatible(prompt, system, temperature)
    elif provider == "ollama":
        return await _call_ollama(prompt, system, temperature)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


async def _call_openai_compatible(prompt: str, system: str, temperature: float) -> str:
    """Call OpenAI-compatible APIs (Groq, Mistral, OpenAI)."""
    provider = settings.llm_provider.lower()

    # Determine the base URL based on provider
    base_urls = {
        "groq": "https://api.groq.com/openai",
        "mistral": "https://api.mistral.ai",
        "openai": "https://api.openai.com",
    }
    base_url = settings.llm_api_url or base_urls.get(provider, settings.llm_api_url)
    url = f"{base_url}/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {settings.llm_api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": settings.llm_model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
        "top_p": 0.9,
        "max_tokens": 1500,
    }

    import asyncio
    async with httpx.AsyncClient(timeout=300.0) as client:
        max_retries = 4
        for attempt in range(max_retries):
            try:
                response = await client.post(url, json=payload, headers=headers)
                if response.status_code == 429 and attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 20  # Waits 20s, 40s, 60s
                    logger.warning(f"Rate limited (429) by {provider}. Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
            except httpx.HTTPStatusError as e:
                if attempt == max_retries - 1 or getattr(e.response, "status_code", None) != 429:
                    logger.error(f"LLM API error ({provider}): {e.response.status_code} — {e.response.text}")
                    raise
            except httpx.ConnectError:
                logger.error(f"Cannot connect to {provider} API at {url}")
                raise
            except (KeyError, IndexError) as e:
                logger.error(f"Unexpected response format from {provider}: {e}")
                raise


async def _call_ollama(prompt: str, system: str, temperature: float) -> str:
    """Call the Ollama native API."""
    url = f"{settings.llm_api_url}/api/generate"
    payload = {
        "model": settings.llm_model,
        "prompt": prompt,
        "system": system,
        "stream": False,
        "options": {
            "temperature": temperature,
            "top_p": 0.9,
            "top_k": 40,
            "num_predict": 4096,
        },
    }

    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "").strip()
        except httpx.HTTPStatusError as e:
            logger.error(f"Ollama API error: {e.response.status_code} — {e.response.text}")
            raise
        except httpx.ConnectError:
            logger.error(f"Cannot connect to Ollama at {settings.llm_api_url}. Is the server running?")
            raise


def parse_json_from_llm(text: str, fallback_topic: str = "Untitled Post") -> dict:
    """
    Extract JSON from LLM output, handling common formatting issues.
    LLMs sometimes wrap JSON in markdown code blocks or add extra text.
    """
    # Try to find JSON in code blocks first
    json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if json_match:
        text = json_match.group(1)

    # Try to find raw JSON object
    json_match = re.search(r"\{.*\}", text, re.DOTALL)
    if json_match:
        text = json_match.group(0)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse JSON from LLM output: {text[:200]}...")
        # Return a fallback structure
        return {
            "title": fallback_topic.title(),
            "meta_description": f"Learn more about {fallback_topic} in this comprehensive post.",
            "sections": [
                {"heading": f"What's the Deal With {fallback_topic.title()}?", "points": [f"Main topic overview for {fallback_topic}"]},
                {"heading": "The Core Strategy", "points": ["Important information"]},
                {"heading": "Final Thoughts", "points": ["Final thoughts"]},
            ],
        }


async def generate_outline(topic: str, keywords: List[str]) -> dict:
    """Step 1: Generate a structured outline from topic + keywords."""
    prompt = OUTLINE_PROMPT.format(
        topic=topic,
        keywords=", ".join(keywords),
    )
    logger.info(f"Generating outline for topic: {topic}")
    raw = await call_llm(prompt, temperature=0.9)
    outline = parse_json_from_llm(raw, fallback_topic=topic)
    logger.info(f"Outline generated: {outline.get('title', 'Unknown')}")
    return outline


async def generate_intro(title: str, section_headings: List[str], keywords: List[str]) -> str:
    """Step 2: Write the introduction."""
    prompt = INTRO_PROMPT.format(
        title=title,
        section_headings=", ".join(section_headings),
        keywords=", ".join(keywords),
    )
    logger.info("Generating introduction...")
    return await call_llm(prompt, temperature=0.7)


async def generate_section(
    title: str,
    heading: str,
    points: List[str],
    keywords: List[str],
    previous_sections: List[str],
    word_count: int = 250,
) -> str:
    """Step 3: Expand a single section into full prose."""
    prompt = SECTION_PROMPT.format(
        title=title,
        heading=heading,
        points="\n".join(f"- {p}" for p in points),
        keywords=", ".join(keywords),
        previous_sections=", ".join(previous_sections) if previous_sections else "None (this is the first section)",
        word_count=word_count,
    )
    logger.info(f"Generating section: {heading}")
    return await call_llm(prompt, temperature=0.8)


async def generate_conclusion(title: str, section_headings: List[str], keywords: List[str]) -> str:
    """Step 4: Write the conclusion."""
    prompt = CONCLUSION_PROMPT.format(
        title=title,
        section_headings=", ".join(section_headings),
        keywords=", ".join(keywords),
    )
    logger.info("Generating conclusion...")
    return await call_llm(prompt, temperature=0.7)


async def generate_blog_post(
    topic: str,
    keywords: List[str],
    target_word_count: int = 1200,
) -> dict:
    """
    Full blog post generation pipeline.
    
    Returns a dict with:
    - title: str
    - slug: str
    - content: str (full markdown)
    - meta_description: str
    - keywords: list[str]
    - word_count: int
    """

    # Step 1: Generate outline
    outline = await generate_outline(topic, keywords)
    title = outline.get("title", f"Guide to {topic}")
    meta_description = outline.get("meta_description", "")
    sections = outline.get("sections", [])

    if not sections:
        logger.warning("No sections in outline, using fallback")
        sections = [
            {"heading": "Getting Started", "points": [f"Overview of {topic}"]},
            {"heading": "Key Concepts", "points": [f"Important aspects of {topic}"]},
            {"heading": "Practical Tips", "points": [f"How to apply {topic}"]},
        ]

    # Calculate words per section to hit target
    # Reserve ~250 words for intro + conclusion
    body_word_target = target_word_count - 250
    words_per_section = max(150, body_word_target // len(sections))

    # Step 2: Generate introduction
    section_headings = [s["heading"] for s in sections]
    intro = await generate_intro(title, section_headings, keywords)

    # Step 3: Generate each section
    body_parts = []
    previous_headings = []
    for section in sections:
        heading = section["heading"]
        points = section.get("points", [])
        section_text = await generate_section(
            title=title,
            heading=heading,
            points=points,
            keywords=keywords,
            previous_sections=previous_headings,
            word_count=words_per_section,
        )
        body_parts.append(f"## {heading}\n\n{section_text}")
        previous_headings.append(heading)

    # Step 4: Generate conclusion
    conclusion = await generate_conclusion(title, section_headings, keywords)

    # Step 5: Assemble the full markdown document
    full_content = f"{intro}\n\n" + "\n\n".join(body_parts) + f"\n\n## Final Thoughts\n\n{conclusion}"

    # Generate slug from title
    slug = slugify(title, max_length=80)

    # Count words
    word_count = len(full_content.split())

    logger.info(f"Blog post generated: '{title}' ({word_count} words)")

    return {
        "title": title,
        "slug": slug,
        "content": full_content,
        "meta_description": meta_description,
        "keywords": keywords,
        "word_count": word_count,
    }
