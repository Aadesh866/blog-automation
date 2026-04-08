"""
post_processor.py — Anti-AI-detection rewriting pipeline.

This module takes raw LLM output and rewrites it to avoid AI detection tools
like GPTZero, Originality.ai, etc. The strategy mirrors what services like
Opace AI Scribe do:

1. SENTENCE VARIATION: Break monotonous rhythm by mixing 5-word punches with complex sentences
2. ACTIVE VOICE: Convert passive constructions to active
3. CONTRACTIONS: Replace formal word pairs with everyday contractions
4. FILLER REMOVAL: Strip AI-telltale phrases and transitions
5. HUMAN FLOURISHES: Inject parenthetical asides, colloquialisms, rhetorical Qs
6. PARAGRAPH RESHAPING: Vary paragraph lengths for natural reading rhythm
7. LLM REWRITE: Final pass through the LLM with anti-AI prompt
"""

import re
import random
import logging
from typing import List

logger = logging.getLogger(__name__)

# ───────────────────────────────────────────────
# AI-telltale phrases to strip or replace
# ───────────────────────────────────────────────

AI_PHRASES = [
    (r"\bIn today's (?:digital |fast-paced |modern |ever-evolving )?(?:world|landscape|era|age)\b", "Right now"),
    (r"\bIt's worth noting that\b", "Here's the thing —"),
    (r"\bIt is worth noting that\b", "Here's the thing —"),
    (r"\bMoreover,?\b", "Plus,"),
    (r"\bFurthermore,?\b", "And"),
    (r"\bIn conclusion,?\b", "So,"),
    (r"\bTo sum up,?\b", "Bottom line —"),
    (r"\bAll in all,?\b", "Look,"),
    (r"\bDelve into\b", "dig into"),
    (r"\bdelve into\b", "dig into"),
    (r"\bDive deep into\b", "get into"),
    (r"\bdive deep into\b", "get into"),
    (r"\bLeverage\b", "Use"),
    (r"\bleverage\b", "use"),
    (r"\bUtilize\b", "Use"),
    (r"\butilize\b", "use"),
    (r"\bcomprehensive guide\b", "guide"),
    (r"\bComprehensive guide\b", "Guide"),
    (r"\bgame[- ]changer\b", "big deal"),
    (r"\bGame[- ]changer\b", "Big deal"),
    (r"\bparadigm shift\b", "major change"),
    (r"\bsynergy\b", "teamwork"),
    (r"\bholistic approach\b", "complete approach"),
    (r"\bseamless(?:ly)?\b", "smooth"),
    (r"\brobust\b", "solid"),
    (r"\bcutting[- ]edge\b", "latest"),
    (r"\bstate[- ]of[- ]the[- ]art\b", "modern"),
    (r"\bplethora of\b", "plenty of"),
    (r"\bmyriad of\b", "many"),
    (r"\bIn the realm of\b", "In"),
    (r"\bin the realm of\b", "in"),
    (r"\bNavigating the\b", "Dealing with"),
    (r"\bnavigating the\b", "dealing with"),
    (r"\bUnlocking the\b", "Getting the"),
    (r"\bunlocking the\b", "getting the"),
    (r"\bThis article (?:will |shall )?(?:explore|discuss|examine|cover)\b", "We'll look at"),
    (r"\bthis article (?:will |shall )?(?:explore|discuss|examine|cover)\b", "we'll look at"),
    (r"\bLet's (?:delve|dive) (?:deep )?into\b", "Let's get into"),
    (r"\bWithout further ado\b", "So"),
]

# Formal → contraction replacements
CONTRACTIONS = [
    (r"\bdo not\b", "don't"),
    (r"\bDo not\b", "Don't"),
    (r"\bcannot\b", "can't"),
    (r"\bCannot\b", "Can't"),
    (r"\bwill not\b", "won't"),
    (r"\bWill not\b", "Won't"),
    (r"\bshould not\b", "shouldn't"),
    (r"\bShould not\b", "Shouldn't"),
    (r"\bwould not\b", "wouldn't"),
    (r"\bWould not\b", "Wouldn't"),
    (r"\bcould not\b", "couldn't"),
    (r"\bCould not\b", "Couldn't"),
    (r"\bit is\b", "it's"),
    (r"\bIt is\b", "It's"),
    (r"\bthat is\b", "that's"),
    (r"\bThat is\b", "That's"),
    (r"\bthey are\b", "they're"),
    (r"\bThey are\b", "They're"),
    (r"\bwe are\b", "we're"),
    (r"\bWe are\b", "We're"),
    (r"\byou are\b", "you're"),
    (r"\bYou are\b", "You're"),
    (r"\bI am\b", "I'm"),
    (r"\bI have\b", "I've"),
    (r"\bI will\b", "I'll"),
    (r"\bthere is\b", "there's"),
    (r"\bThere is\b", "There's"),
    (r"\bwhat is\b", "what's"),
    (r"\bWhat is\b", "What's"),
    (r"\bhere is\b", "here's"),
    (r"\bHere is\b", "Here's"),
]

# Conversational transitions to randomly inject between paragraphs
TRANSITIONS = [
    "Here's where it gets interesting.",
    "And honestly?",
    "Now, you might be thinking — ",
    "But wait, there's more to it.",
    "The real kicker?",
    "I've seen this play out firsthand.",
    "This one surprised me.",
    "Let me break this down.",
    "Real talk —",
    "Quick story.",
]


def strip_ai_phrases(text: str) -> str:
    """Remove or replace known AI-generated phrases."""
    for pattern, replacement in AI_PHRASES:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text


def apply_contractions(text: str) -> str:
    """Replace formal word pairs with contractions for natural tone."""
    for pattern, replacement in CONTRACTIONS:
        text = re.sub(pattern, replacement, text)
    return text


def vary_sentence_length(text: str) -> str:
    """
    Break up monotonous sentence rhythm.
    Split very long sentences (30+ words) and occasionally merge very short ones.
    """
    sentences = re.split(r'(?<=[.!?])\s+', text)
    result = []

    for sentence in sentences:
        words = sentence.split()
        # Split sentences longer than 30 words at natural break points
        if len(words) > 30:
            # Find a conjunction or comma to split at
            mid = len(words) // 2
            split_point = None
            for i in range(mid - 3, mid + 3):
                if 0 < i < len(words) and words[i].lower() in (
                    'and', 'but', 'which', 'while', 'although', 'because', 'however',
                ):
                    split_point = i
                    break
            if split_point:
                first = ' '.join(words[:split_point])
                second = ' '.join(words[split_point:])
                # Capitalize the second part
                second = second[0].upper() + second[1:] if second else second
                if not first.endswith(('.', '!', '?')):
                    first += '.'
                result.append(first)
                result.append(second)
                continue
        result.append(sentence)

    return ' '.join(result)


def reshape_paragraphs(text: str) -> str:
    """
    Vary paragraph length for natural rhythm.
    Occasionally split long paragraphs or merge very short ones.
    """
    paragraphs = text.split('\n\n')
    result = []

    for para in paragraphs:
        # Skip headings and empty lines
        if para.strip().startswith('#') or not para.strip():
            result.append(para)
            continue

        sentences = re.split(r'(?<=[.!?])\s+', para.strip())

        # Split paragraphs with 6+ sentences
        if len(sentences) > 6:
            mid = len(sentences) // 2
            result.append(' '.join(sentences[:mid]))
            result.append(' '.join(sentences[mid:]))
        else:
            result.append(para)

    return '\n\n'.join(result)


def inject_transitions(text: str, max_injections: int = 2) -> str:
    """
    Randomly inject conversational transitions between paragraphs
    to break the AI-typical monotone flow.
    """
    paragraphs = text.split('\n\n')
    if len(paragraphs) < 4:
        return text

    # Pick random positions (not first, not last, not adjacent)
    eligible = [i for i in range(2, len(paragraphs) - 1)
                if not paragraphs[i].strip().startswith('#')]

    if not eligible:
        return text

    inject_count = min(max_injections, len(eligible))
    positions = random.sample(eligible, inject_count)

    for pos in sorted(positions, reverse=True):
        transition = random.choice(TRANSITIONS)
        paragraphs.insert(pos, transition)

    return '\n\n'.join(paragraphs)


def calculate_quality_score(text: str) -> float:
    """
    Calculate a content quality score (0-100) based on various metrics.
    Used for the admin dashboard.
    """
    score = 0.0
    words = text.split()
    word_count = len(words)
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]

    # Word count score (target: 1000-1500)
    if 1000 <= word_count <= 1500:
        score += 25
    elif 800 <= word_count <= 2000:
        score += 15
    else:
        score += 5

    # Sentence length variety
    if sentences:
        lengths = [len(s.split()) for s in sentences]
        avg_len = sum(lengths) / len(lengths)
        variance = sum((l - avg_len) ** 2 for l in lengths) / len(lengths)
        if variance > 30:  # Good variety
            score += 20
        elif variance > 15:
            score += 10
        else:
            score += 5

    # Has subheadings (H2s)
    h2_count = text.count('## ')
    if h2_count >= 3:
        score += 15
    elif h2_count >= 2:
        score += 10

    # Paragraph variety
    paragraphs = [p for p in text.split('\n\n') if p.strip() and not p.strip().startswith('#')]
    if paragraphs:
        para_lengths = [len(p.split()) for p in paragraphs]
        para_variance = sum((l - sum(para_lengths)/len(para_lengths)) ** 2
                           for l in para_lengths) / len(para_lengths) if para_lengths else 0
        if para_variance > 100:
            score += 15
        elif para_variance > 50:
            score += 10

    # Contains questions (engagement)
    question_count = text.count('?')
    if question_count >= 3:
        score += 10
    elif question_count >= 1:
        score += 5

    # No AI-telltale phrases remaining
    ai_phrase_count = sum(1 for pattern, _ in AI_PHRASES if re.search(pattern, text, re.IGNORECASE))
    if ai_phrase_count == 0:
        score += 15
    elif ai_phrase_count <= 2:
        score += 8

    return min(100.0, score)


def process_post(content: str) -> tuple[str, float]:
    """
    Full post-processing pipeline. Takes raw LLM content and returns
    human-sounding text + quality score.

    Returns: (processed_content, quality_score)
    """
    logger.info("Post-processing: stripping AI phrases...")
    content = strip_ai_phrases(content)

    logger.info("Post-processing: applying contractions...")
    content = apply_contractions(content)

    logger.info("Post-processing: varying sentence length...")
    content = vary_sentence_length(content)

    logger.info("Post-processing: reshaping paragraphs...")
    content = reshape_paragraphs(content)

    logger.info("Post-processing: injecting transitions...")
    content = inject_transitions(content)

    quality_score = calculate_quality_score(content)
    logger.info(f"Post-processing complete. Quality score: {quality_score}/100")

    return content, quality_score
