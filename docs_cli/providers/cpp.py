import requests
import requests_cache
from bs4 import BeautifulSoup
from markdownify import markdownify as md
from .base import BaseProvider

class CppProvider(BaseProvider):
    """
    C++ Documentation Provider
    """
    def search(self, query: str, force_refresh: bool = False, force_anomaly: bool = False):
        """
        Parses C++ official documentation to search for standard library functions.

        Returns:
            tuple: (url, result, cache_status)
            cache_status can be:
                - True: served from cache (normal)
                - False: fetched online (normal)
                - "anomaly": all requests failed, but data somehow was acquired
                - None: unknown state
        """
        # Query cleaner
        clean_query = query.replace("std::", "").strip().lower()

        # URLs list
        urls = [
            f"https://en.cppreference.com/w/cpp/{clean_query}",
            f"https://en.cppreference.com/w/cpp/container/{clean_query}",
            f"https://en.cppreference.com/w/cpp/string/{clean_query}",
            f"https://en.cppreference.com/w/cpp/algorithm/{clean_query}",
            f"https://en.cppreference.com/w/cpp/keyword/{clean_query}",
            f"https://en.cppreference.com/w/cpp/language/{clean_query}",
            f"https://en.cppreference.com/w/cpp/types/{clean_query}",
            f"https://en.cppreference.com/w/cpp/io/{clean_query}",
            f"https://en.cppreference.com/w/cpp/memory/{clean_query}",
            f"https://en.cppreference.com/w/cpp/utility/{clean_query}",
            f"https://en.cppreference.com/w/cpp/header/{clean_query}",
        ]

        session = requests_cache.get_cache()

        # Reqeusts tracking
        total_requests = 0
        failed_requests = 0
        any_data_found = False  # Track if we found any data
        is_from_cache = None
        headers = {'User-Agent': 'DocsCLI/0.2'}

        for url in urls:
            try:
                if force_refresh and session:
                    # Create a request object with the same parameters to get the correct cache key
                    cache_key = session.create_key(
                        request=requests.Request('GET', url, headers = headers).prepare()
                    )
                    session.delete(cache_key)

                # DEBUG
                # print(f"Trying URL: {url}")

                # Add User_Agent AND expire_after
                response = requests.get(url, headers = headers, allow_redirects=True)
                total_requests += 1

                response.encoding = 'utf-8'

                # Determine if the response was served from cache
                is_from_cache = getattr(response, 'from_cache', False)

                if response.status_code != 200:
                    failed_requests += 1
                    continue

                if "mw-content-text" not in response.text:
                    failed_requests += 1
                    continue
                
                final_url = response.url
                url_result, text_result, _ = self._parse_page(response.text, final_url, clean_query, is_from_cache)

                if url_result:
                    any_data_found = True
                    if force_anomaly:
                        return url_result, text_result, "anomaly"
                    return url_result, text_result, is_from_cache
                
                # If page exists (200) but parsing failed - try next URL
                continue

            except Exception:
                failed_requests += 1
                continue

        if total_requests > 0 and failed_requests == total_requests and any_data_found:
            # Anomaly: all requests failed but we got data somehow
            if is_from_cache:
                return None, "Not found in C++ standard library documentation.", "anomaly"
            else:
                return None, "Failed to retrieve documentation data from all sources.", None

        return None, "Not found in C++ standard library documentation.", None
    
    def _parse_page(self, html, url, query, is_from_cache):
        """
        Parses the HTML content of a C++ documentation page.

        Returns:
            tuple: (url, result, cache_status)
        """
        soup = BeautifulSoup(html, 'lxml')

        # Main content of CppReference is layed out in <div id="mw-content-text">
        content = soup.find('div', {"id": "mw-content-text"})

        if content:
            text_parts = []

            # Search all paragraphs
            paras = content.find_all("p")

            # Filter out completely empty paragraphs
            valid_paras = [p for p in paras if p.get_text(strip=True)]

            for p in valid_paras[:3]: # limit to first 3 paragraphs
                text_parts.append(str(p))

            if not text_parts:
                return None, "Found page but could not parse content.", is_from_cache
            
            full_html = "".join(text_parts)

            # Convert to Markdown
            text = md(full_html)

            return url, text.strip(), is_from_cache
        
        return None, "Parse Error", is_from_cache