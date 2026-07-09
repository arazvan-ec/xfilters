"""Pluggable ingestion adapters: raw input -> list[Bookmark]."""

from .base import Ingestor, autodetect, extract_tweet_id

__all__ = ["Ingestor", "autodetect", "extract_tweet_id"]
