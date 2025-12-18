"""
DevDocs.io Provider
Universal provider supporting 50+ languages with auto-version discovery.
"""
import json
from .base import BaseProvider
from ..utils import (
    USER_AGENT,
    handle_cache,
    fetch_url,
    parse_html,
    remove_html_garbage,
    html_to_markdown,
)


class DevDocsProvider(BaseProvider):
    """
    Universal Provider for DevDocs.io architecture.
    Supports 50+ languages with auto-version discovery.
    """
    BASE_URL = "https://devdocs.io"
    DOCS_URL = "https://devdocs.io/docs.json"  # List of all available languages
    CDN_URL = "https://documents.devdocs.io"

    # DevDocs-specific garbage selectors
    GARBAGE_SELECTORS = [
        # Compatibility tables and sections
        "#browser_compatibility", ".bc-table", ".compatibility", ".htab",
        # Specifications and formal definitions
        "#specifications", ".spec-table", "#formal_definition",
        # Other common clutter
        "#see_also", ".see-also", ".item-footer",
    ]

    def __init__(self, language_slug: str):
        self.slug = language_slug
        self.headers = {'User-Agent': USER_AGENT}

    def _resolve_real_slug(self, bad_slug: str, force_refresh: bool) -> str | None:
        """
        Download docs.json and search for the latest version of the language.
        
        Args:
            bad_slug: The slug that returned 403/404
            force_refresh: Whether to bypass cache
            
        Returns:
            The correct slug or None if not found
        """
        try:
            handle_cache(self.DOCS_URL, force_refresh, self.headers)
            response, _ = fetch_url(self.DOCS_URL, headers=self.headers)

            if response.status_code != 200:
                return None

            all_docs = response.json()
            candidates = []

            for doc in all_docs:
                slug = doc.get('slug', '')
                if slug == bad_slug or slug.startswith(f"{bad_slug}~"):
                    candidates.append(slug)

            if not candidates:
                return None

            # Sort to get the latest version (lexicographically)
            candidates.sort(reverse=True)
            return candidates[0]

        except Exception:
            return None

    def _fetch_from_db_fallback(self, path: str, force_refresh: bool) -> str | None:
        """
        Download the full db.json file if individual HTML files are unavailable.
        
        Args:
            path: The path within the documentation
            force_refresh: Whether to bypass cache
            
        Returns:
            HTML content for the specific path, or None
        """
        db_url = f"{self.CDN_URL}/{self.slug}/db.json"

        try:
            handle_cache(db_url, force_refresh, self.headers)
            response, _ = fetch_url(db_url, headers=self.headers)

            if response.status_code != 200:
                return None

            db_data = response.json()
            return db_data.get(path)

        except Exception:
            return None

    def _parse_html(self, html: str) -> str:
        """
        Parse HTML content and convert to Markdown.
        
        Args:
            html: Raw HTML content
            
        Returns:
            Cleaned markdown text
        """
        soup = parse_html(html)

        # Find main content area
        content = soup.find(class_="_content") or soup

        # Remove DevDocs-specific garbage
        remove_html_garbage(content, extra_selectors=self.GARBAGE_SELECTORS)

        # Convert to markdown (preserve tables and links for DevDocs)
        return html_to_markdown(str(content))

    def search(self, query: str, force_refresh: bool = False) -> tuple:
        """
        Search DevDocs.io for the given query.

        Args:
            query: The term to search for
            force_refresh: If True, bypass cache and fetch fresh data

        Returns:
            tuple: (url, result, is_from_cache)
            - url: Documentation URL or None if not found
            - result: Markdown text or error message
            - is_from_cache: True if from cache, False if online, None if unknown
        """
        is_from_cache = None
        index_url = f"{self.CDN_URL}/{self.slug}/index.json"

        try:
            handle_cache(index_url, force_refresh, self.headers)
            response, _ = fetch_url(index_url, headers=self.headers)

            # Auto-discovery: if 403/404, slug might be outdated
            if response.status_code in [403, 404]:
                new_slug = self._resolve_real_slug(self.slug, force_refresh)
                if new_slug and new_slug != self.slug:
                    self.slug = new_slug
                    index_url = f"{self.CDN_URL}/{self.slug}/index.json"
                    handle_cache(index_url, force_refresh, self.headers)
                    response, _ = fetch_url(index_url, headers=self.headers)

            if response.status_code != 200:
                return None, f"Could not load index for '{self.slug}' (Status: {response.status_code})", None

            # Parse the JSON index
            try:
                data = response.json()
                entries = data.get('entries', [])
            except json.JSONDecodeError:
                return None, "Failed to parse DevDocs index JSON.", None

            # Search logic: exact match → starts with → contains
            query_lower = query.lower()

            found_entry = next(
                (item for item in entries if item["name"].lower() == query_lower),
                None
            )
            if not found_entry:
                found_entry = next(
                    (item for item in entries if item["name"].lower().startswith(query_lower)),
                    None
                )
            if not found_entry:
                found_entry = next(
                    (item for item in entries if query_lower in item["name"].lower()),
                    None
                )

            if not found_entry:
                return None, f"Not found '{query}' in {self.slug} documentation.", None

            # Build URLs
            doc_path = found_entry["path"]
            final_url = f"{self.BASE_URL}/{self.slug}/{doc_path}"

            # Attempt 1: Download individual HTML file
            path_no_anchor = doc_path.split('#')[0]
            html_url = f"{self.CDN_URL}/{self.slug}/{path_no_anchor}.html"

            handle_cache(html_url, force_refresh, self.headers)
            doc_response, is_from_cache = fetch_url(html_url, headers=self.headers)

            if doc_response.status_code == 200:
                text = self._parse_html(doc_response.text)
                return final_url, text, is_from_cache

            # Attempt 2: Fallback to db.json (for Ruby, Rails, etc.)
            db_content = self._fetch_from_db_fallback(path_no_anchor, force_refresh)

            if db_content:
                text = self._parse_html(db_content)
                return final_url, text, is_from_cache

            return None, f"Failed to download content (Status: {doc_response.status_code})", None

        except Exception as e:
            return None, str(e), None