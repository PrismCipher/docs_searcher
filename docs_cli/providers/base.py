"""
Base Provider Interface
All documentation providers must implement this interface.
"""
from abc import ABC, abstractmethod


class BaseProvider(ABC):
    """Abstract base class for documentation providers."""

    @abstractmethod
    def search(self, query: str, force_refresh: bool = False) -> tuple:
        """
        Search for documentation on the given query.

        Args:
            query: The term to search for (function name, class, etc.)
            force_refresh: If True, bypass cache and fetch fresh data

        Returns:
            tuple: (url, result, is_from_cache)
            - url: Documentation URL or None if not found
            - result: Markdown text, error message, or suggestions dict
            - is_from_cache: True if from cache, False if online, None if unknown
        """
        pass