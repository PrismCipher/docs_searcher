"""
C++ Documentation Provider
Searches cppreference.com for standard library functions.
"""
from .base import BaseProvider
from ..utils import (
    handle_cache,
    fetch_url,
    parse_html,
    html_to_markdown,
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

        # Get first 3 non-empty paragraphs
        paras = content.find_all("p")
        valid_paras = [p for p in paras if p.get_text(strip=True)][:3]

        if not valid_paras:
            return None, "Found page but could not parse content."

        full_html = "".join(str(p) for p in valid_paras)
        text = html_to_markdown(full_html)

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

        for url in urls:
            try:
                # Handle cache invalidation
                handle_cache(url, force_refresh)

                # Fetch the page
                response, is_from_cache = fetch_url(url)

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

        return None, "Not found in C++ standard library documentation.", None