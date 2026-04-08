"""
link_injector.py — Automatically injects internal and external hyperlinks into blog content.

SEO STRATEGY:
- Internal links help distribute page authority and keep readers on site
- External links to authority domains improve E-E-A-T signals
- Links are placed on natural anchor text, not forced keyword stuffing
- Density is limited to avoid over-optimisation penalties (max 3 internal + 2 external per post)
- Links are only injected on the first occurrence of each keyword
"""

import re
import logging
from typing import Dict

logger = logging.getLogger(__name__)

# Maximum links per post to avoid over-optimisation
MAX_INTERNAL_LINKS = 3
MAX_EXTERNAL_LINKS = 2


def inject_links(
    content: str,
    internal_links: Dict[str, str],
    external_links: Dict[str, str],
    site_domain: str = "",
) -> str:
    """
    Inject hyperlinks into blog content based on keyword-to-URL mappings.

    Args:
        content: The blog post markdown content
        internal_links: keyword → relative URL mapping (e.g., {"react hooks": "/blog/react-hooks"})
        external_links: keyword → full URL mapping (e.g., {"Next.js": "https://nextjs.org"})
        site_domain: The site's domain for constructing full internal URLs

    Returns:
        Content with hyperlinks injected
    """
    if not internal_links and not external_links:
        return content

    # Split content into lines to preserve headings (don't link inside headings)
    lines = content.split('\n')
    processed_lines = []
    internal_count = 0
    external_count = 0
    used_keywords = set()

    for line in lines:
        # Skip headings and empty lines — don't inject links there
        if line.strip().startswith('#') or not line.strip():
            processed_lines.append(line)
            continue

        # Skip lines that already contain links
        if '[' in line and '](' in line:
            processed_lines.append(line)
            continue

        # Inject internal links (highest priority)
        if internal_count < MAX_INTERNAL_LINKS:
            for keyword, url in internal_links.items():
                if keyword.lower() in used_keywords:
                    continue
                if internal_count >= MAX_INTERNAL_LINKS:
                    break

                # Case-insensitive search for the keyword, but only match whole words
                pattern = re.compile(
                    r'\b(' + re.escape(keyword) + r')\b',
                    re.IGNORECASE
                )

                if pattern.search(line):
                    # Build the full URL
                    full_url = f"{site_domain}{url}" if site_domain and not url.startswith('http') else url
                    # Replace only the FIRST occurrence
                    line = pattern.sub(
                        lambda m: f'[{m.group(1)}]({full_url})',
                        line,
                        count=1
                    )
                    internal_count += 1
                    used_keywords.add(keyword.lower())
                    logger.debug(f"Injected internal link: '{keyword}' → {full_url}")

        # Inject external links
        if external_count < MAX_EXTERNAL_LINKS:
            for keyword, url in external_links.items():
                if keyword.lower() in used_keywords:
                    continue
                if external_count >= MAX_EXTERNAL_LINKS:
                    break

                pattern = re.compile(
                    r'\b(' + re.escape(keyword) + r')\b',
                    re.IGNORECASE
                )

                if pattern.search(line):
                    line = pattern.sub(
                        lambda m: f'[{m.group(1)}]({url})',
                        line,
                        count=1
                    )
                    external_count += 1
                    used_keywords.add(keyword.lower())
                    logger.debug(f"Injected external link: '{keyword}' → {url}")

        processed_lines.append(line)

    result = '\n'.join(processed_lines)
    logger.info(f"Links injected: {internal_count} internal, {external_count} external")
    return result
