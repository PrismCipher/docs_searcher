"""
Python Documentation Provider
Searches Python's official documentation for built-in functions and types.
"""
import difflib
from .base import BaseProvider
from ..utils import (
    handle_cache,
    fetch_url,
    parse_html,
    html_to_markdown,
    get_suggestions,
)


class PythonProvider(BaseProvider):
    """Provider for Python official documentation (docs.python.org)"""

    SEARCH_URLS = [
        "https://docs.python.org/3/library/functions.html",
        "https://docs.python.org/3/library/stdtypes.html"
    ]

    def _parse_description(self, element, url: str, query: str) -> tuple:
        """
        Parse the description of a documentation element.
        
        Args:
            element: BeautifulSoup element containing the function definition
            url: Base URL of the documentation page
            query: The function name being searched
        
        Returns:
            tuple: (full_url, markdown_text) or None if not found
        """
        description_tag = element.find_next_sibling("dd")
        if description_tag:
            html_content = str(description_tag)
            text = html_to_markdown(html_content)
            text = text.lstrip(" :\n")
            return f"{url}#{query}", text
        return None

    def search(self, query: str, force_refresh: bool = False) -> tuple:
        """
        Search Python's official documentation for built-in functions.

        Args:
            query: Function name to search (e.g., "print", "len")
            force_refresh: If True, bypass cache and fetch fresh data

        Returns:
            tuple: (url, result, is_from_cache)
            - url: Documentation URL or None if not found
            - result: Markdown text, error message, or suggestions dict
            - is_from_cache: True if from cache, False if online, None if unknown
        """
        clean_query = query.strip("()").lower()
        all_seen_ids = []
        is_from_cache = None

        try:
            for url in self.SEARCH_URLS:
                try:
                    # Handle cache invalidation
                    handle_cache(url, force_refresh)

                    # Fetch the page
                    response, is_from_cache = fetch_url(url)

                    if response.status_code != 200:
                        continue

                    # Parse HTML
                    soup = parse_html(response.text)

                    # Search for element by ID (Python docs use function name as ID)
                    element = soup.find(id=clean_query)

                    if element:
                        result = self._parse_description(element, url, clean_query)
                        if result:
                            url_result, text_result = result
                            return url_result, text_result, is_from_cache
                        return None, "Function found but could not parse description.", None

                    # Collect all IDs for suggestions
                    page_ids = [dt.get('id') for dt in soup.find_all('dt') if dt.get('id')]
                    all_seen_ids.extend(page_ids)

                except Exception:
                    continue

            # No data retrieved at all
            if not all_seen_ids:
                return None, "Failed to retrieve documentation. No cached or online data available.", None

            # Function not found - try to suggest alternatives
            suggestions = get_suggestions(clean_query, all_seen_ids)
            if suggestions:
                return None, suggestions, None

            return None, "Function not found in Python built-ins.", None

        except Exception as e:
            return None, f"Unexpected error: {str(e)}", None