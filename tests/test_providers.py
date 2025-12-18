import pytest
from docs_cli.providers import get_provider

def normalize(text):
    return " ".join(text.split())

# Python Provider Test
def test_python_search():
    """
    Test that Python provider can find and parse the 'len' function.
    Verifies correct URL and presence of key description phrases.
    """
    provider = get_provider("python")
    assert provider is not None, "Python Provider is None"
    url, result, _ = provider.search("len")
    assert url == "https://docs.python.org/3/library/functions.html#len"
    assert "Return the length" in result
    assert "argument may be a sequence" in normalize(result)

def test_python_search_force_refresh():
    """
    Test that Python provider correctly fetches fresh data when force_refresh=True.
    Verifies that data comes from online source, not cache.
    """
    provider = get_provider("python")
    assert provider is not None, "Python Provider is None"
    url, result, is_cached = provider.search("len", force_refresh=True)
    assert url is not None
    assert is_cached is False  # Must be online, not cached

# C++ Provider Test
def test_cpp_search():
    """
    Test that C++ provider can find and parse the 'vector' documentation.
    Verifies correct domain (cppreference.com) and presence of relevant terms.
    """
    provider = get_provider("cpp")
    assert provider is not None, "C++ Provider is None"
    url, result, _ = provider.search("vector")
    assert "cppreference.com" in url
    assert "vector" in url
    assert "dynamic array" in result.lower() or "element" in result.lower()

def test_cpp_search_force_refresh():
    """
    Test that C++ provider correctly fetches fresh data when force_refresh=True.
    Verifies that data comes from online source, not cache.
    Uses 'map' instead of 'vector' to avoid cache conflicts with other tests.
    """
    provider = get_provider("cpp")
    assert provider is not None, "C++ Provider is None"
    url, result, is_cached = provider.search("map", force_refresh=True)
    assert url is not None
    assert is_cached is False  # Must be online, not cached

# DevDocs Provider Test
def test_devdocs_search():
    """
    Test that DevDocs provider can find Rust documentation for 'Vec'.
    Verifies correct domain and presence of vector-related terminology.
    """
    provider = get_provider("rust")
    assert provider is not None, "DevDocs:Rust provider is None"
    url, result, _ = provider.search("Vec")
    assert "devdocs.io" in url or "rust-lang.org" in url
    assert "contiguous growable array" in result.lower() or "vector" in result.lower()

def test_devdocs_search_force_refresh():
    """
    Test that DevDocs (Rust) provider correctly fetches fresh data when force_refresh=True.
    Verifies that data comes from online source, not cache.
    """
    provider = get_provider("rust")
    assert provider is not None, "DevDocs:Rust provider is None"
    url, result, is_cached = provider.search("Vec", force_refresh=True)
    assert url is not None
    assert is_cached is False  # Must be online, not cached


# DevDocs Provider Fallback Test
def test_devdocs_fallback_search():
    """
    Test that DevDocs provider can handle Ruby documentation via db.json fallback.
    Ruby uses the "heavy" method (db.json) instead of individual HTML files.
    """
    provider = get_provider("ruby")
    assert provider is not None, "DevDocs:Ruby provider is None"
    url, result, _ = provider.search("print")
    assert result is not None
    assert len(result) > 50
    assert "print" in result

def test_devdocs_fallback_search_force_refresh():
    """
    Test that DevDocs (Ruby) provider correctly fetches fresh data when force_refresh=True.
    Note: Ruby uses db.json which is a large file, so this test may take longer.
    """
    provider = get_provider("ruby")
    assert provider is not None, "DevDocs:Ruby provider is None"
    url, result, is_cached = provider.search("print", force_refresh=True)
    assert url is not None
    assert result is not None
    assert is_cached is False  # Must be online, not cached

# Sphinx Provider Test
def test_sphinx_search():
    """
    Test that Sphinx provider can find pandas documentation for 'read_csv'.
    Verifies correct domain (pandas.pydata.org) and function description.
    """
    provider = get_provider("pandas")
    assert provider is not None, "Sphinx:Pandas Provider is None"
    url, result, _ = provider.search("read_csv")
    assert "pandas.pydata.org" in url
    assert "read_csv" in url
    assert "Read a comma-separated values" in result

def test_sphinx_search_force_refresh():
    """
    Test that Sphinx (Pandas) provider correctly fetches fresh data when force_refresh=True.
    Verifies that data comes from online source, not cache.
    """
    provider = get_provider("pandas")
    assert provider is not None, "Sphinx:Pandas Provider is None"
    url, result, is_cached = provider.search("read_csv", force_refresh=True)
    assert url is not None
    assert is_cached is False  # Must be online, not cached

# Error Handling Test
def test_unknown_function():
    """
    Test that provider correctly handles queries for non-existent functions.
    Should return None for URL and either an error message or suggestions.
    """
    provider = get_provider("python")
    url, result, _ = provider.search("fun")
    assert url is None
    assert result is not None