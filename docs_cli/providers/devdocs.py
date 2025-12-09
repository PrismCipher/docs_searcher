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
    Supports 50+ languages with auto-version discovery.
    """
    BASE_URL = "https://devdocs.io"
    DOCS_URL = "https://devdocs.io/docs.json"  # List of all available languages and versions
    CDN_URL = "https://documents.devdocs.io"
    
    def __init__(self, language_slug: str):
        self.slug = language_slug
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

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

        # Build the index URL for the specified language
        index_url = f"{self.CDN_URL}/{self.slug}/index.json"

        try:
            if force_refresh and session:
                session.delete(urls=[index_url])

            response = requests.get(index_url, headers=self.headers)

            # Auto-discovery: if we got 403/404, the slug might be outdated
            if response.status_code in [403, 404]:
                new_slug = self._resolve_real_slug(self.slug, force_refresh)
                if new_slug and new_slug != self.slug:
                    self.slug = new_slug
                    index_url = f"{self.CDN_URL}/{self.slug}/index.json"
                    response = requests.get(index_url, headers=self.headers)

            if response.status_code != 200:
                return None, f"Could not load index for '{self.slug}' (Status: {response.status_code})", None
            
            # Parse the JSON index
            try:
                data = response.json()
                entries = data.get('entries', [])
            except json.JSONDecodeError:
                return None, "Failed to parse DevDocs index JSON.", None

            # Search logic: try exact match, then starts with, then contains
            query_lower = query.lower()
            
            # Exact match
            found_entry = next((item for item in entries if item["name"].lower() == query_lower), None)
            
            # Starts with
            if not found_entry:
                found_entry = next((item for item in entries if item["name"].lower().startswith(query_lower)), None)
            
            # Contains
            if not found_entry:
                found_entry = next((item for item in entries if query_lower in item["name"].lower()), None)

            if not found_entry:
                return None, f"Not found '{query}' in {self.slug} documentation.", None
            
            # Got the path
            doc_path = found_entry["path"]
            final_url = f"{self.BASE_URL}/{self.slug}/{doc_path}"
            
            # Content loading logic:
            # Attempt 1: "Light" method - download individual HTML file
            # (Works for CSS, HTML, JS, Rust, and most modern docs)
            path_no_anchor = doc_path.split('#')[0]
            html_url = f"{self.CDN_URL}/{self.slug}/{path_no_anchor}.html"

            if force_refresh and session:
                session.delete(urls=[html_url])

            doc_response = requests.get(html_url, headers=self.headers)
            is_from_cache = getattr(doc_response, 'from_cache', False)

            if doc_response.status_code == 200:
                text = self._parse_html(doc_response.text)
                if force_anomaly:
                    return final_url, text, "anomaly"
                return final_url, text, is_from_cache
            
            # Attempt 2: "Heavy" method (Fallback) - download full db.json
            # (Required for Ruby, Rails, and others that don't serve individual files)
            # If we got 401/403/404 on the HTML file, the server requires us to use the DB
            db_content = self._fetch_from_db_fallback(path_no_anchor, force_refresh)
            
            if db_content:
                text = self._parse_html(db_content)
                # If we got it from DB, cache status reflects the HTML request
                return final_url, text, is_from_cache

            return None, f"Failed to download content via HTML (Status: {doc_response.status_code}) or DB fallback.", None
        
        except Exception as e:
            return None, str(e), None

    def _fetch_from_db_fallback(self, path, force_refresh):
        """
        Downloads the full db.json file for the language if individual HTML files are unavailable.
        Returns the HTML content for the specific path.
        """
        db_url = f"{self.CDN_URL}/{self.slug}/db.json"
        session = requests_cache.get_cache()

        try:
            # db.json is large, so we rely heavily on requests cache
            if force_refresh and session:
                session.delete(urls=[db_url])
            
            response = requests.get(db_url, headers=self.headers)
            
            if response.status_code != 200:
                return None
            
            db_data = response.json()

            return db_data.get(path)
            
        except Exception:
            return None

    def _resolve_real_slug(self, bad_slug, force_refresh):
        """
        Downloads docs.json and searches for the latest version of the language.
        """
        try:
            if force_refresh:
                session = requests_cache.get_cache()
                if session:
                    session.delete(urls=[self.DOCS_URL])

            resp = requests.get(self.DOCS_URL, headers=self.headers)
            if resp.status_code != 200:
                return None
            
            all_docs = resp.json()
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
    
    def _parse_html(self, html):
        """
        Parses the HTML content and converts it to Markdown.
        """
        soup = BeautifulSoup(html, 'lxml')
        
        # Find main content area
        content = soup.find(class_="_content") or soup

        # List of selectors for elements to remove
        garbage_selectors = [
            "nav", "footer", "header", "script", "style", "svg", "button", "iframe", "form",
            ".sidebar", ".ads", ".print-only", ".visually-hidden", ".toc", ".breadcrumb",
            
            # Compatibility tables and sections
            "#browser_compatibility", ".bc-table", ".compatibility", ".htab",

            # Specifications and formal definitions
            "#specifications", ".spec-table", "#formal_definition",
            
            # Other common clutter
            "#see_also", ".see-also", ".item-footer"
        ]

        # Remove garbage elements
        for selector in garbage_selectors:
            if selector.startswith('.'):
                for tag in content.find_all(class_=selector[1:]):
                    tag.decompose()
            elif selector.startswith('#'):
                for tag in content.find_all(id=selector[1:]):
                    tag.decompose()
            else:
                for tag in content.find_all(selector):
                    tag.decompose()

        # Remove all tables (they break terminal formatting)
        for table in content.find_all("table"):
            table.decompose()
            
        # Remove headers that introduce compatibility/spec sections
        for header in content.find_all(["h2", "h3"], string=re.compile(r"(Browser compatibility|Specifications|Formal syntax)", re.I)):
            header.decompose()

        # Convert HTML to Markdown
        # strip=['img', 'a'] removes images and links (cleaner terminal output)
        markdown_text = md(str(content), heading_style="ATX", strip=['img', 'a'])
        
        # Post-processing: remove horizontal rules
        markdown_text = re.sub(r'^\s*[-*_]{3,}\s*$', '', markdown_text, flags=re.MULTILINE)
        
        # Normalize multiple newlines
        markdown_text = re.sub(r'\n{3,}', '\n\n', markdown_text)

        return markdown_text.strip()