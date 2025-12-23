"""
Shared utility functions for all providers.
Provides unified handling for caching, encoding, HTML parsing, and markdown conversion.
"""
import re
import requests
import requests_cache
import difflib
from bs4 import BeautifulSoup
from markdownify import markdownify as md

# =============================================================================
# Global Configuration
# =============================================================================

VERSION = "0.3"
USER_AGENT = f"DocsCLI/{VERSION}"
USER_AGENT_BROWSER = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Encoding settings (can be modified at runtime via CLI flags)
DEFAULT_ENCODING = "utf-8"
AUTO_DETECT_ENCODING = False


# =============================================================================
# Cache Utilities
# =============================================================================

def handle_cache(url: str, force_refresh: bool, headers: dict = None) -> None:
    """
    Unified cache handling for all providers.
    Deletes cached entry for URL if force_refresh is True.
    
    Args:
        url: The URL to potentially remove from cache
        force_refresh: If True, delete the URL from cache
        headers: Optional headers dict (if None, uses default User-Agent for cache key)
    """
    if not force_refresh:
        return
    
    session = requests_cache.get_cache()
    if not session:
        return
    
    # Use default headers if none provided (must match fetch_url behavior)
    if headers is None:
        headers = {'User-Agent': USER_AGENT}
    
    # Create cache key with headers (headers affect cache key in requests-cache)
    try:
        cache_key = session.create_key(
            request=requests.Request('GET', url, headers=headers).prepare()
        )
        session.delete(cache_key)
    except Exception:
        # Fallback to simple URL-based deletion
        session.delete(urls=[url])


# =============================================================================
# Request Utilities
# =============================================================================

def fetch_url(url: str, headers: dict = None, encoding: str = None) -> tuple:
    """
    Fetch URL with consistent encoding handling.
    
    Args:
        url: The URL to fetch
        headers: Optional headers dict (if None, uses default User-Agent)
        encoding: Force specific encoding (None = use global settings)
    
    Returns:
        tuple: (response, is_from_cache)
        - response: requests.Response object with proper encoding set
        - is_from_cache: True if served from cache, False otherwise
    """
    # Use default headers if none provided
    if headers is None:
        headers = {'User-Agent': USER_AGENT}
    
    response = requests.get(url, headers=headers, allow_redirects=True)
    
    # Apply encoding
    if encoding:
        response.encoding = encoding
    elif not AUTO_DETECT_ENCODING:
        response.encoding = DEFAULT_ENCODING
    # else: let requests auto-detect
    
    is_from_cache = getattr(response, 'from_cache', False)
    return response, is_from_cache


def get_headers(use_browser_ua: bool = False) -> dict:
    """
    Get standard headers for requests.
    
    Args:
        use_browser_ua: If True, use browser-like User-Agent (for sites that block bots)
    
    Returns:
        dict: Headers dictionary
    """
    return {
        'User-Agent': USER_AGENT_BROWSER if use_browser_ua else USER_AGENT
    }


# =============================================================================
# HTML Parsing Utilities
# =============================================================================

def parse_html(html: str) -> BeautifulSoup:
    """
    Parse HTML string into BeautifulSoup object.
    
    Args:
        html: HTML string to parse (already decoded to Unicode)
    
    Returns:
        BeautifulSoup object
    
    Note:
        from_encoding is not used here because the input is already a
        decoded string. Encoding is handled in fetch_url() instead.
    """
    return BeautifulSoup(html, 'lxml')


def remove_html_garbage(content: BeautifulSoup, extra_selectors: list = None) -> None:
    """
    Remove unwanted HTML elements from BeautifulSoup content.
    Modifies content in-place.
    
    Args:
        content: BeautifulSoup element to clean
        extra_selectors: Additional selectors to remove beyond the defaults.
            Supports:
            - ".classname" for class selectors
            - "#idname" for ID selectors
            - "tagname" for tag selectors
            - "tag.class" for combined selectors (uses .select())
    """
    # Default garbage selectors (always removed)
    default_selectors = [
        "nav", "footer", "header", "script", "style", "svg", "button",
        "iframe", "form", ".sidebar", ".ads", ".print-only",
        ".visually-hidden", ".toc", ".breadcrumb",
    ]
    
    # Combine defaults with extras
    selectors = default_selectors + (extra_selectors or [])
    
    for selector in selectors:
        if '.' in selector and not selector.startswith('.'):
            # Combined selector like "a.headerlink" - use CSS selector
            for tag in content.select(selector):
                tag.decompose()
        elif selector.startswith('.'):
            # Class selector
            for tag in content.find_all(class_=selector[1:]):
                tag.decompose()
        elif selector.startswith('#'):
            # ID selector
            for tag in content.find_all(id=selector[1:]):
                tag.decompose()
        else:
            # Tag selector
            for tag in content.find_all(selector):
                tag.decompose()


# =============================================================================
# Markdown Conversion Utilities
# =============================================================================

def html_to_markdown(
    html_content,
    preserve_links: bool = True,
    preserve_tables: bool = True,
    preserve_images: bool = False
) -> str:
    """
    Convert HTML to Markdown with configurable options.
    
    Args:
        html_content: HTML string or BeautifulSoup object
        preserve_links: Keep URLs in output (default: True)
        preserve_tables: Keep tables in output (default: True)
        preserve_images: Keep images in output (default: False)
    
    Returns:
        Cleaned markdown text
    """
    strip_elements = []
    
    if not preserve_images:
        strip_elements.append('img')
    
    if not preserve_links:
        strip_elements.append('a')
    
    if not preserve_tables:
        strip_elements.append('table')
    
    # Convert to markdown
    if strip_elements:
        markdown_text = md(str(html_content), heading_style="ATX", strip=strip_elements)
    else:
        markdown_text = md(str(html_content), heading_style="ATX")
    
    # Common cleanup
    markdown_text = clean_markdown(markdown_text)
    
    return markdown_text


def clean_markdown(text: str) -> str:
    """
    Clean up markdown text by removing artifacts and normalizing whitespace.
    
    Args:
        text: Raw markdown text
    
    Returns:
        Cleaned markdown text
    """
    # Remove horizontal rules (---, ***, ___)
    text = re.sub(r'^\s*[-*_]{3,}\s*$', '', text, flags=re.MULTILINE)
    
    # Strip leading/trailing spaces from each line
    lines = [line.strip() for line in text.splitlines()]
    text = "\n".join(lines)
    
    # Remove excessive blank lines (3+ newlines → 2 newlines)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Remove paragraph symbols (¶) that may remain from docs
    text = text.replace("¶", "")
    
    # Fix spaces before punctuation
    text = re.sub(r'\s+([.,;!?])', r'\1', text)
    
    return text.strip()


# =============================================================================
# Text Processing Utilities
# =============================================================================

def normalize_text(text: str) -> str:
    """
    Normalize text by collapsing whitespace.
    Useful for comparisons and tests.
    
    Args:
        text: Text to normalize
    
    Returns:
        Normalized text with single spaces
    """
    return " ".join(text.split())

# =============================================================================
# Suggestion Utilities
# =============================================================================

def get_suggestions(query: str, available_names: list, n: int = 3, cutoff: float = 0.6) -> dict | None:
    """
    Find similar names to suggest when exact match is not found.
    
    Args:
        query: The search term that wasn't found
        available_names: List of valid names to search through
        n: Maximum number of suggestions to return
        cutoff: Minimum similarity ratio (0.0 to 1.0)
    
    Returns:
        dict with "type": "did_you_mean" and "matches" list, or None if no matches
    """
    if not available_names:
        return None
    
    matches = difflib.get_close_matches(query.lower(), [name.lower() for name in available_names], n=n, cutoff=cutoff)
    
    if matches:
        # Find original case versions
        original_matches = []
        for match in matches:
            for name in available_names:
                if name.lower() == match:
                    original_matches.append(name)
                    break
            else:
                original_matches.append(match)
        
        return {"type": "did_you_mean", "matches": original_matches}
    
    return None