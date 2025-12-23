"""
C++ Documentation Provider
Searches cppreference.com for standard library functions.
"""
from .base import BaseProvider
from ..utils import (
    handle_cache,
    fetch_url,
    parse_html,
    remove_html_garbage,
    html_to_markdown,
    get_suggestions,
)


class CppProvider(BaseProvider):
    """Provider for C++ documentation (cppreference.com)"""

    # URL patterns to search for C++ documentation
    URL_PATTERNS = [
        "https://en.cppreference.com/w/cpp/{}",
        "https://en.cppreference.com/w/cpp/container/{}",
        "https://en.cppreference.com/w/cpp/string/{}",
        "https://en.cppreference.com/w/cpp/algorithm/{}",
        "https://en.cppreference.com/w/cpp/keyword/{}",
        "https://en.cppreference.com/w/cpp/language/{}",
        "https://en.cppreference.com/w/cpp/types/{}",
        "https://en.cppreference.com/w/cpp/io/{}",
        "https://en.cppreference.com/w/cpp/memory/{}",
        "https://en.cppreference.com/w/cpp/utility/{}",
        "https://en.cppreference.com/w/cpp/header/{}",
    ]

    # Common C++ standard library items for suggestions
    COMMON_ITEMS = [
        "vector", "map", "set", "list", "deque", "array", "string",
        "unordered_map", "unordered_set", "queue", "stack", "priority_queue",
        "pair", "tuple", "optional", "variant", "any",
        "sort", "find", "copy", "transform", "accumulate", "count",
        "unique_ptr", "shared_ptr", "weak_ptr", "make_unique", "make_shared",
        "cout", "cin", "endl", "cerr", "ifstream", "ofstream",
        "thread", "mutex", "lock_guard", "async", "future",
        "int", "long", "double", "float", "char", "bool", "void",
        "class", "struct", "enum", "union", "namespace", "template",
        "if", "else", "for", "while", "do", "switch", "case", "break", "continue", "return",
    ]

    # CppReference-specific garbage selectors
    GARBAGE_SELECTORS = [
        ".t-navbar",          # Navigation bar
        ".mw-editsection",    # Edit section links
        "#toc",               # Table of contents
        ".t-dcl-rev-aux",     # Revision aux
        ".noprint",           # Print-hidden elements
    ]

    def _parse_page(self, html: str, url: str) -> tuple:
        """
        Parse the HTML content of a C++ documentation page.

        Args:
            html: Raw HTML content
            url: The URL of the page

        Returns:
            tuple: (url, markdown_text) or (None, error_message)
        """
        soup = parse_html(html)

        # Main content of CppReference is in <div id="mw-content-text">
        content = soup.find('div', {"id": "mw-content-text"})

        if not content:
            return None, "Parse Error"

        # Remove CppReference-specific garbage
        remove_html_garbage(content, extra_selectors=self.GARBAGE_SELECTORS)

        # Convert full content to markdown (preserve tables and links)
        text = html_to_markdown(str(content))

        if not text.strip():
            return None, "Found page but could not parse content."

        return url, text

    def search(self, query: str, force_refresh: bool = False) -> tuple:
        """
        Search C++ documentation for standard library functions.

        Args:
            query: Function/class name to search (e.g., "vector", "std::map")
            force_refresh: If True, bypass cache and fetch fresh data

        Returns:
            tuple: (url, result, is_from_cache)
            - url: Documentation URL or None if not found
            - result: Markdown text or error message
            - is_from_cache: True if from cache, False if online, None if unknown
        """
        # Clean the query (remove std:: prefix)
        clean_query = query.replace("std::", "").strip().lower()
        is_from_cache = None

        # Generate URLs to try
        urls = [pattern.format(clean_query) for pattern in self.URL_PATTERNS]

        if force_refresh:
            for url in urls:
                handle_cache(url, force_refresh=True)

        for url in urls:
            try:
                # Fetch the page
                response, is_from_cache = fetch_url(url)

                # When force_refresh was used, override the cache status
                if force_refresh:
                    is_from_cache = False

                if response.status_code != 200:
                    continue

                # Check if page has content
                if "mw-content-text" not in response.text:
                    continue

                # Parse the page
                final_url = response.url  # Handle redirects
                url_result, text_result = self._parse_page(response.text, final_url)

                if url_result:
                    return url_result, text_result, is_from_cache

            except Exception:
                continue

        # Not found - try to suggest alternatives
        suggestions = get_suggestions(clean_query, self.COMMON_ITEMS)
        if suggestions:
            return None, suggestions, None

        return None, "Not found in C++ standard library documentation.", None