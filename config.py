"""Shared configuration for SecondSelf."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent

load_dotenv(PROJECT_ROOT / ".env")


def _path(name: str, default: str) -> Path:
    value = os.getenv(name, default)
    path = Path(value)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path


def _float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


RAW_DIR = _path("RAW_DIR", "raw")
WIKI_DIR = _path("WIKI_DIR", "wiki")
EMBEDDINGS_DIR = _path("EMBEDDINGS_DIR", "embeddings")
GRAPH_PATH = _path("GRAPH_PATH", "graph.json")
STATIC_DIR = _path("STATIC_DIR", "static")

PARA_CATEGORIES = ("Projects", "Areas", "Resources", "Archives")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

SIMILARITY_THRESHOLD = _float("SIMILARITY_THRESHOLD", 0.75)
RAG_TOP_K = _int("RAG_TOP_K", 5)
RAG_SIMILARITY_THRESHOLD = _float("RAG_SIMILARITY_THRESHOLD", 0.5)

MAX_CAPTURE_FILE_BYTES = _int("MAX_CAPTURE_FILE_BYTES", 10 * 1024 * 1024)
URL_FETCH_TIMEOUT_SECONDS = _int("URL_FETCH_TIMEOUT_SECONDS", 10)
MAX_LINKS_PER_NOTE = _int("MAX_LINKS_PER_NOTE", 10)


def ensure_directories() -> None:
    """Create data directories if they do not exist."""
    for path in (
        RAW_DIR,
        WIKI_DIR,
        EMBEDDINGS_DIR,
        STATIC_DIR,
        *(WIKI_DIR / category for category in PARA_CATEGORIES),
    ):
        path.mkdir(parents=True, exist_ok=True)


ensure_directories()
