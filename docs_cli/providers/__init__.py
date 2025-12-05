import requests_cache
from pathlib import Path
from datetime import timedelta
from .python import PythonProvider
from .cpp import CppProvider

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

def get_provider(lang: str):
    """Returns the provider class for the selected language or None"""
    return PROVIDERS.get(lang.lower())