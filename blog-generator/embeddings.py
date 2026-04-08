"""
embeddings.py — Generate text embeddings using the remote Ollama API.
Uses nomic-embed-text model (768 dimensions) for pgvector storage.
These embeddings power semantic search on the frontend.
"""

import logging
from typing import List

import httpx

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


async def generate_embedding(text: str) -> List[float]:
    """
    Generate a 768-dimensional embedding vector for the given text.

    Supports:
    - "ollama": Uses remote Ollama embeddings API (nomic-embed-text)
    - "none": Skip embedding generation (returns empty list)

    Args:
        text: The text to embed (usually title + content excerpt)

    Returns:
        List of 768 floats representing the embedding vector, or empty list
    """
    if settings.embed_provider == "none":
        logger.debug("Embedding generation skipped (EMBED_PROVIDER=none)")
        return []

    url = f"{settings.embed_api_url}/api/embeddings"
    payload = {
        "model": settings.llm_embed_model,
        "prompt": text[:8000],  # Truncate to avoid exceeding context window
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            embedding = data.get("embedding", [])

            if not embedding:
                logger.warning("Empty embedding returned from API")
                return []

            logger.debug(f"Generated embedding: {len(embedding)} dimensions")
            return embedding

        except httpx.HTTPStatusError as e:
            logger.error(f"Embedding API error: {e.response.status_code}")
            return []
        except httpx.ConnectError:
            logger.error(f"Cannot connect to embedding API at {settings.embed_api_url}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error generating embedding: {e}")
            return []


async def generate_post_embedding(title: str, content: str, keywords: List[str]) -> List[float]:
    """
    Generate an embedding for a blog post by combining title, keywords, and
    a content excerpt. This combined text gives the embedding semantic context
    from all key parts of the post.

    Args:
        title: Post title
        content: Full post content (will be truncated)
        keywords: List of target keywords

    Returns:
        768-dim embedding vector
    """
    # Combine title + keywords + first ~2000 chars of content for a rich embedding
    combined_text = f"{title}\n\nKeywords: {', '.join(keywords)}\n\n{content[:2000]}"
    return await generate_embedding(combined_text)
