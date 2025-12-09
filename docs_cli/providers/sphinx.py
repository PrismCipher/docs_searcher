import requests
import requests_cache
import zlib
import re
from bs4 import BeautifulSoup
from markdownify import markdownify as md
from .base import BaseProvider

class SphinxProvider(BaseProvider):
    """
    Provider for Sphinx-generated documentation (Pandas, NumPy, Django, etc.).
    Parses 'objects.inv' binary inventory files.
    """
    def __init__(self, name: str, base_url: str):
        self.name = name
        self.base_url = base_url.rstrip("/")  # Ensure no trailing slash
        self.inventory_url = f"{self.base_url}/objects.inv"
        #self.headers = {'User-Agent': 'DocsCLI/0.2'}
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

    def search(self, query: str, force_refresh: bool = False, force_anomaly: bool = False):
        session = requests_cache.get_cache()
        is_from_cache = None

        # Fetch and parse the inventory
        try: 
            inventory = self._get_inventory(force_refresh)
        except Exception as e:
            return None, f"Failed to load inventory for {self.name}: {e}", None
        
        # Search for the query in the inventory
        # Precise search
        matches = [name for name in inventory.keys() if name == query]

        # If not, try endswith
        if not matches:
            matches = [name for name in inventory.keys() if name.endswith(f".{query}")]

        # If not, try close match
        if not matches:
            matches = [name for name in inventory.keys() if query in name]

        # If not found, blame microsoft
        if not matches:
            return None, f"Not found '{query}' in {self.name} inventory.", None
        
        best_match = min(matches, key=len)
        relative_path = inventory[best_match]

        full_url = f"{self.base_url}/{relative_path}"

        request_url = full_url.split('#')[0]

        # Download page
        try:
            if force_refresh and session:
                session.delete(urls=[request_url])

            response = requests.get(request_url, headers=self.headers)
            is_from_cache = getattr(response, 'from_cache', False)

            if response.status_code == 200:
                response.encoding = 'utf-8'
                text = self._parse_html(response.text, query)

                if force_anomaly:
                    return full_url, text, "anomaly"
                
                return full_url, text, is_from_cache
            
            return None, f"Found match '{best_match}' but URL failed (404).\nTried fetching: {request_url}", None
        
        except Exception as e:
            return None, str(e), None
        
    def _get_inventory(self, force_refresh):
        """
        Downloads and decompresses the Sphinx objects.inv file.
        Returns a dict: { "function_name": "relative_url" }
        """
        session = requests_cache.get_cache()

        if force_refresh and session:
            session.delete(urls=[self.inventory_url])

        # objects.inv is a binary file, so we have to use stream=True and content
        response = requests.get(self.inventory_url, headers=self.headers)

        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}")
        
        # Sphinx Inventory Parsing Logic
        inventory = {}
        content = response.content

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

            # We have to use Regex pattern for Sphinx v2 inventory lines
            pattern = re.compile(r"^(.+?)\s+(\S+:\S+)\s+(-?\d+)\s+(\S+)\s*(.*)$")

            for line in lines:
                parts = pattern.match(line.rstrip())
                if parts:
                    name = parts.group(1)
                    uri = parts.group(4)

                    if uri.endswith("$"):
                        uri = uri[:-1] + name

                    inventory[name] = uri

        except Exception as e:
            print(f"Debug parsing error: {e}")
            pass

        return inventory
    
    def _parse_html(self, html, query):
        soup = BeautifulSoup(html, 'lxml')

        # Spinx contains data inside blockquote, div.body or article
        content = soup.find(class_="body") or soup.find(class_="document") or soup.find("article") or soup

        # Removing garbage
        garbage_selector = [
            ".sphinxsidebar", ".related", ".footer", ".admonition-title", 
            "nav", "script", "style", ".headerlink",
            ".prev-next-bottom", ".table-of-contents",
            "a.headerlink"
        ]

        for selector in garbage_selector:
            for tag in content.select(selector):
                tag.decompose()

        for dl in content.find_all ("dl", class_="field-list"):
            dl.name = "div"

        # Convert HTML to Markdown
        markdown_text = md(str(content), heading_style="ATX", strip=['img', 'a', 'table'])

        # Post-processing with regex
        markdown_text = re.sub(r'^\s*[-*_]{3,}\s*$', '', markdown_text, flags=re.MULTILINE)
        
        # Strip leading/trailing spaces to prevent accidental code blocks
        lines = [line.strip() for line in markdown_text.splitlines()]
        markdown_text = "\n".join(lines)
        
        # Remove excessive blank lines
        markdown_text = re.sub(r'\n{3,}', '\n\n', markdown_text)
        
        # Remove permalink symbols if any remain
        markdown_text = markdown_text.replace("¶", "")

        return markdown_text.strip()