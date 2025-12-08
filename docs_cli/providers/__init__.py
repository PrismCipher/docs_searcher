import requests_cache
from pathlib import Path
from datetime import timedelta
from .python import PythonProvider
from .cpp import CppProvider
from .devdocs import DevDocsProvider

# GLOBAL CACHE SETUP
CACHE_DIR = Path.home() / ".docs_cli"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
cache_path = CACHE_DIR / "http_cache"
requests_cache.install_cache(str(cache_path), expire_after=timedelta(hours=24))

# PROVIDERS REGISTRY
PROVIDERS = {
    "python": PythonProvider(),
    "py": PythonProvider(),  # Alias
    "cpp": CppProvider(),
    "c++": CppProvider(),    # Alias
}

# DEVDOCS.IO SUPPORTED LANGUAGES
DEVDOCS_SUPPORTED = [
    "rust", "go", "javascript", "js", "html", "css", "java", "php", "ruby", "c", "dom"
]

# DEVDOCS.IO ALIAS MAPPING
DEVDOCS_ALIASES = {
    "c#": "c_sharp",
    "cs": "c_sharp",
    "csharp": "c_sharp",
    "fsharp": "f_sharp",
    "js": "javascript",
    "ts": "typescript",
    "typescript": "typescript",
}

def get_provider(lang: str):
    """Returns the provider class for the selected language or None"""
    lang = lang.lower()

    if lang in PROVIDERS:
        return PROVIDERS[lang]
    
    devdocs_lang = DEVDOCS_ALIASES.get(lang, lang)

    return DevDocsProvider(devdocs_lang)