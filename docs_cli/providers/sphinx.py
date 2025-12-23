"""
Sphinx Documentation Provider
Supports Sphinx-generated documentation (Pandas, NumPy, Django, etc.).
Parses 'objects.inv' binary inventory files.
"""
import zlib
import re
from .base import BaseProvider
from ..utils import (
    USER_AGENT,
    handle_cache,
    fetch_url,
    parse_html,
    remove_html_garbage,
    html_to_markdown,
    get_suggestions,
)


class SphinxProvider(BaseProvider):
    """
    Provider for Sphinx-generated documentation.
    Parses 'objects.inv' binary inventory files to locate documentation.
    """

    # Sphinx-specific garbage selectors
    GARBAGE_SELECTORS = [
        ".sphinxsidebar", ".related", ".footer", ".admonition-title",
        ".prev-next-bottom", ".table-of-contents", "a.headerlink",
    ]

    def __init__(self, name: str, base_url: str):
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.inventory_url = f"{self.base_url}/objects.inv"
        self.headers = {'User-Agent': USER_AGENT}

    def _get_inventory(self, force_refresh: bool) -> dict:
        """
        Download and decompress the Sphinx objects.inv file.
        
        Args:
            force_refresh: Whether to bypass cache
            
        Returns:
            dict: { "function_name": "relative_url" }
        """
        handle_cache(self.inventory_url, force_refresh, self.headers)

        # objects.inv is binary, so we use raw content
        response, _ = fetch_url(self.inventory_url, headers=self.headers)

        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}")

        inventory = {}
        content = response.content

        # Find zlib compressed section
        delimiter = b'zlib'
        start_index = content.find(delimiter)

        if start_index == -1:
            return {}

        # Skip header line
        start_index = content.find(b'\n', start_index) + 1
        compressed_data = content[start_index:]

        try:
            decompressed = zlib.decompress(compressed_data)
            lines = decompressed.decode('utf-8').splitlines()

            # Sphinx v2 inventory line pattern
            pattern = re.compile(r"^(.+?)\s+(\S+:\S+)\s+(-?\d+)\s+(\S+)\s*(.*)$")

            for line in lines:
                parts = pattern.match(line.rstrip())
                if parts:
                    name = parts.group(1)
                    uri = parts.group(4)

                    # Handle $ substitution
                    if uri.endswith("$"):
                        uri = uri[:-1] + name

                    inventory[name] = uri

        except Exception:
            pass

        return inventory

    def _parse_html(self, html: str) -> str:
        """
        Parse HTML content and convert to Markdown.
        
        Args:
            html: Raw HTML content
            
        Returns:
            Cleaned markdown text
        """
        soup = parse_html(html)

        # Sphinx content is in div.body, div.document, or article
        content = (
            soup.find(class_="body") or
            soup.find(class_="document") or
            soup.find("article") or
            soup
        )

        # Remove garbage
        remove_html_garbage(content, extra_selectors=self.GARBAGE_SELECTORS)

        # Convert dl.field-list to div for better markdown
        for dl in content.find_all("dl", class_="field-list"):
            dl.name = "div"

        # Convert to markdown (preserve tables)
        markdown_text = html_to_markdown(str(content))

        # Remove permalink symbols
        markdown_text = markdown_text.replace("¶", "")

        return markdown_text

    def search(self, query: str, force_refresh: bool = False) -> tuple:
        """
        Search Sphinx-generated documentation.

        Args:
            query: Function/class name to search
            force_refresh: If True, bypass cache and fetch fresh data

        Returns:
            tuple: (url, result, is_from_cache)
            - url: Documentation URL or None if not found
            - result: Markdown text or error message
            - is_from_cache: True if from cache, False if online, None if unknown
        """
        is_from_cache = None

        # Fetch and parse the inventory
        try:
            inventory = self._get_inventory(force_refresh)
        except Exception as e:
            return None, f"Failed to load inventory for {self.name}: {e}", None

        # Get all available names for suggestions
        available_names = list(inventory.keys())

        # Search for the query: exact → endswith → contains
        matches = [name for name in inventory.keys() if name == query]

        if not matches:
            matches = [name for name in inventory.keys() if name.endswith(f".{query}")]

        if not matches:
            matches = [name for name in inventory.keys() if query in name]

        if not matches:
            # Try to suggest alternatives
            suggestions = get_suggestions(query, available_names)
            if suggestions:
                return None, suggestions, None
            return None, f"Not found '{query}' in {self.name} inventory.", None

        # Get shortest match (most specific)
        best_match = min(matches, key=len)
        relative_path = inventory[best_match]
        full_url = f"{self.base_url}/{relative_path}"
        request_url = full_url.split('#')[0]

        # Download page
        try:
            handle_cache(request_url, force_refresh, self.headers)
            response, is_from_cache = fetch_url(request_url, headers=self.headers)

            if response.status_code == 200:
                text = self._parse_html(response.text)
                return full_url, text, is_from_cache

            return None, f"Found match '{best_match}' but URL failed (404).\nTried: {request_url}", None

        except Exception as e:
            return None, str(e), None