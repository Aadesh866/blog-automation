"""
config.py — Central configuration loader.
Reads environment variables and sites.json for multi-site support.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Optional
from pydantic import BaseModel
from pydantic_settings import BaseSettings


class SiteConfig(BaseModel):
    """Configuration for a single website."""
    id: str
    name: str
    domain: str
    supabase_url: str
    supabase_key: str
    supabase_service_key: str
    sanity_project_id: str
    sanity_dataset: str = "production"
    sanity_token: str
    posts_per_cycle: int = 3
    topics: List[str] = []
    keywords: List[str] = []
    internal_links: Dict[str, str] = {}
    external_links: Dict[str, str] = {}


class Settings(BaseSettings):
    """Global settings from environment variables."""
    # LLM Provider: "groq", "mistral", "openai", or "ollama"
    llm_provider: str = "groq"

    # API configuration
    llm_api_url: str = "https://api.groq.com/openai"  # Groq default
    llm_api_key: str = ""  # Required for groq/mistral/openai
    llm_model: str = "llama-3.1-8b-instant"  # Groq model name
    llm_embed_model: str = "nomic-embed-text"  # For Ollama embeddings

    # Embedding provider: "ollama" or "none" (skip embeddings for now)
    embed_provider: str = "none"
    embed_api_url: str = "http://localhost:11434"  # Ollama URL for embeddings

    # Generation defaults
    posts_per_cycle: int = 3
    schedule_interval_hours: int = 2
    target_word_count: int = 1200

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# ── Singleton instances ──

_settings: Optional[Settings] = None
_sites: Optional[List[SiteConfig]] = None


def get_settings() -> Settings:
    """Get global settings (cached)."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def get_sites() -> List[SiteConfig]:
    """Load site configurations from sites.json (cached)."""
    global _sites
    if _sites is None:
        sites_path = Path(__file__).parent / "sites.json"
        if not sites_path.exists():
            raise FileNotFoundError(
                f"sites.json not found at {sites_path}. "
                "Copy sites.json.example to sites.json and configure your sites."
            )
        with open(sites_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        _sites = [SiteConfig(**site) for site in data["sites"]]
    return _sites


def get_site_by_id(site_id: str) -> SiteConfig:
    """Get a specific site configuration by ID."""
    for site in get_sites():
        if site.id == site_id:
            return site
    raise ValueError(f"Site '{site_id}' not found in sites.json")


def reload_sites():
    """Force reload sites.json (useful for hot-reloading config)."""
    global _sites
    _sites = None
    return get_sites()
