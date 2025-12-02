import requests
import re
from bs4 import BeautifulSoup
from markdownify import markdownify as md

def get_python_builtin(function_name: str):
    """
    Parses Python's official documentation to search for built-in functions.
    """
    # Target URL (the page where all built-in functions live)
    url = "https://docs.python.org/3/library/functions.html"
    
    try:
        # Make a request to the site
        response = requests.get(url)
        if response.status_code != 200: # Status code 200 means "OK"
            return None, "Error accessing Python docs"

        # Parse the HTML
        soup = BeautifulSoup(response.text, 'lxml')

        # Search for the specific element
        # In Python documentation, each function has an id equal to its name.
        # For example: <dt id="print">
        element = soup.find(id=function_name)

        if element:
            # If we found the function header (dt), we need its description (the next dd tag)
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
                
                return url + f"#{function_name}", text.strip()
        
        return None, "Function not found in built-ins."

    except Exception as e:
        return None, str(e)