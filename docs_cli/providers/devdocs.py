import requests
import requests_cache
import json
import re
from bs4 import BeautifulSoup
from markdownify import markdownify as md
from .base import BaseProvider

class DevDocsProvider(BaseProvider):
    """
    Universal Provider for DevDocs.io architecture.
    Supports 50+ languages.
    """
    BASE_URL = "https://devdocs.io"
    DOCS_URL = "https://devdocs.io/docs.json"
    CDN_URL = "https://documents.devdocs.io"
    
    def __init__(self, language_slug: str):
        self.slug = language_slug
        self.headers = {'User-Agent': 'DocsCLI/0.2'}

    def search(self, query: str, force_refresh: bool = False, force_anomaly: bool = False):
        """
        Searches DevDocs.io for the given query.
        
        Returns:
            tuple: (url, result, cache_status)
            cache_status can be:
                - True: served from cache (normal)
                - False: fetched online (normal)
                - "anomaly": all requests failed, but data somehow was acquired
                - None: unknown state
        """
        session = requests_cache.get_cache()
        is_from_cache = None

        # Fetch the documentation index for the specified language
        index_url = f"{self.CDN_URL}/{self.slug}/index.json"

        try:
            if force_refresh and session:
                session.delete(urls=[index_url])

            response = requests.get(index_url, headers=self.headers)

            if response.status_code != 200:
                return None, f"Could not load documentation index for {self.slug} (Status: {response.status_code})", None
            
            # JSON index of the documentation
            try:
                data = response.json()
                entries = data.get('entries', [])
            except json.JSONDecodeError:
                return None, "Failed to parse DevDocs index JSON.", None

            # Search for the query in the entries
            query_lower = query.lower()

            # Exact match first
            found_entry = next((item for item in entries if item["name"].lower() == query_lower), None)

            # If not found, try partial match
            if not found_entry:
                found_entry = next((item for item in entries if item["name"].lower().startswith(query_lower)), None)

            # If still not found, use contains
            if not found_entry:
                found_entry = next((item for item in entries if query_lower in item["name"].lower()), None)
            
            # Only now, we give up
            if not found_entry:
                return None, f"Not found '{query}' in {self.slug} documentation.", None
            
            # Construct the URL to the documentation page
            doc_path = found_entry["path"]
            final_url = f"{self.BASE_URL}/{self.slug}/{doc_path}" # User-facing URL
            html_url = f"{self.CDN_URL}/{self.slug}/{doc_path}.html" # Parsing HTML content URL

            if force_refresh and session:
                session.delete(urls=[html_url])

            doc_response = requests.get(html_url, headers=self.headers)
            is_from_cache = getattr(doc_response, 'from_cache', False)

            if doc_response.status_code == 200:
                text = self._parse_html(doc_response.text)

                if force_anomaly:
                    return final_url, text, "anomaly"
                
                return final_url, text, is_from_cache
            
            return None, f"Found index entry but failed to download content (Status: {doc_response.status_code}).", None
        
        except Exception as e:
            return None, str(e), None
    
    def _parse_html(self, html):
        """
        Parses the HTML content and converts it to Markdown.
        """
        soup = BeautifulSoup(html, 'lxml')

        # Remove unnecessary elements
        content = soup.find(class_ = "_content") or soup

        garbage_selectors = [
            "nav", "footer", "header", "script", "style", "svg", "button", "iframe",
            ".sidebar", ".ads", ".print-only", ".visually-hidden", ".toc", ".breadcrumb",

            "#browser_compatibility", ".bc_table", ".compatibility",

            "#specifications", ".spec-tables", "#formal_definition",

            "#see_also", ".see-also",
        ]

        for selector in garbage_selectors:
            if selector.startswith('.'):
                for tag in content.find_all(class_=selector[1:]): tag.decompose()
            elif selector.startswith('#'):
                for tag in content.find_all(id=selector[1:]): tag.decompose()
            else:
                for tag in content.find_all(selector): tag.decompose()

        # Convert to markdown
        markdown_text = md(str(content), heading_style="ATX", strip=['img'])

        markdown_text = re.sub(r'^\s*[-*_]{3,}\s*$', '', markdown_text, flags=re.MULTILINE)  # Remove horizontal rules

        markdown_text = re.sub(r'\n{3,}', '\n\n', markdown_text)  # Normalize multiple newlines

        return markdown_text.strip()

