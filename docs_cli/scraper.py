import requests
import re
import difflib
import requests_cache
from bs4 import BeautifulSoup
from markdownify import markdownify as md
from datetime import timedelta

# Set up requests cache to cache responses for 24 hours
requests_cache.install_cache('docs_cache', expire_after=timedelta(hours=24))

def _parse_description(element, url, query):
    """
    Utility function to parse the description of a documentation element.
    """
    description_tag = element.find_next_sibling("dd")
    if description_tag:
        # Take HTML
        html_content = str(description_tag)
        
        # Convert HTML to Markdown
        text = md(html_content, heading_style="ATX")

        # Divide into lines and strip extra spaces
        lines = [line.strip() for line in text.splitlines()]
        text = "\n".join(lines)
        
        # Fix spaces before punctuation
        text = re.sub(r'\s+([.,;!?])', r'\1', text)
        
        # Remove excessive newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remove leading spaces/newlines
        text = text.lstrip(" :\n")
        
        return url + f"#{query}", text.strip()

def get_python_builtin(query: str):
    """
    Parses Python's official documentation to search for built-in functions.
    """
    # Target URL (the page where all built-in functions live)
    search_urls = [
        "https://docs.python.org/3/library/functions.html",
        "https://docs.python.org/3/library/stdtypes.html"
        ]

    # Clean the query
    clean_query = query.strip("()").lower()
    all_seen_ids = [] # To collect all ids for suggestions

    try:
        for url in search_urls:
            # Make a request to the site
            response = requests.get(url)
            if response.status_code != 200: # Status code 200 means "OK"
                return None, "Error accessing Python docs"
            # Parse the HTML
            soup = BeautifulSoup(response.text, 'lxml')

            # Search for the specific element
            # In Python documentation, each function has an id equal to its name.
            # For example: <dt id="print">
            element = soup.find(id=clean_query)

            if element:
                # If we found the function header return result immediately
                result = _parse_description(element, url, clean_query)

                if result:
                    return result
                return None, "Function not found in built-ins."
            
            page_ids = [dt.get('id') for dt in soup.find_all('dt') if dt.get('id')]
            all_seen_ids.extend(page_ids)

        # We did not find the function in any page
        # Search for close matches to suggest with all collected IDs
        # Find 3 closest matches (cutoff=0.6 means 60% similarity)
        matches = difflib.get_close_matches(clean_query, all_seen_ids, n=3, cutoff=0.6)
        
        if matches:
            return None, {"type": "did_you_mean", "matches": matches}
        
        return None, "Function not found."

    except Exception as e:
        return None, str(e)