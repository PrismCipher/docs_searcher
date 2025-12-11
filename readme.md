# Docs CLI

A command-line tool for searching programming documentation directly from your terminal. Supports Python, C++, JavaScript, Rust, and 50+ other languages through multiple documentation sources.

#### Video Demo: [URL]

## Description

Docs CLI is a terminal-based documentation search tool designed to provide quick access to programming language and library documentation without leaving your development environment. The tool implements smart caching to minimize network requests and includes fallback mechanisms to ensure reliable documentation access.

## Features

- **Multiple Documentation Sources**: Queries official documentation sites (Python docs, cppreference.com) and aggregates content from DevDocs.io and Sphinx-based documentation
- **Intelligent Caching**: Responses are cached for 24 hours to reduce network requests and improve response time
- **Fuzzy Matching**: Suggests similar functions when exact matches aren't found
- **Clean Output**: Converts HTML documentation to readable Markdown format, removing navigation elements and advertisements
- **Flexible Command Syntax**: Options can be placed before or after arguments (e.g., `docs python print --force` or `docs --force python print`)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/docs_searcher
   cd docs_searcher
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. (Optional) Install globally to use `docs` command from anywhere:
   ```bash
   pip install -e .
   ```

## Usage

Basic command structure:
```bash
docs [LANGUAGE] [QUERY]
```

### Examples

**Python built-in functions:**
```bash
docs python print
docs python len
```

**C++ standard library:**
```bash
docs cpp vector
docs cpp std::map
```

**Web technologies (via DevDocs):**
```bash
docs js map
docs css flex
docs html canvas
```

**Python libraries (via Sphinx):**
```bash
docs pandas read_csv
docs numpy array
docs django Model
```

**Other languages:**
```bash
docs rust Vec
docs ruby print
docs go fmt
```

### Command Options

- `--force` / `-f`: Bypass cache and fetch fresh documentation
  ```bash
  docs python print --force
  ```

- `--pager` / `-p`: Display output in a pager (useful for long documentation)
  ```bash
  docs pandas DataFrame --pager
  ```

- `--version` / `-v`: Show version information

- `--help`: Display help message and available options

- `info`: Show tool information
  ```bash
  docs info
  ```

## Project Structure

```
docs_searcher/
├── docs_cli/
│   ├── main.py              # CLI interface and command 
│   └── providers/
│       ├── __init__.py      # Provider registry and 
│       ├── base.py          # Abstract base class 
│       ├── python.py        # Python official docs parser
│       ├── cpp.py           # C++ reference 
│       ├── devdocs.py       # DevDocs.io universal 
│       └── sphinx.py        # Sphinx documentation parser
├── tests/
│   └── test_providers.py    # Test suite for all providers
├── requirements.txt
├── setup.py
└── README.md
```

### Provider Details

**PythonProvider** (`python.py`)
- Parses official Python documentation from docs.python.org
- Searches built-in functions and standard types
- Implements fuzzy matching with suggestions for typos

**CppProvider** (`cpp.py`)
- Queries cppreference.com for C++ standard library documentation
- Searches multiple namespaces (container, algorithm, string, etc.)
- Handles both direct lookups and fallback searches

**DevDocsProvider** (`devdocs.py`)
- Universal provider for 50+ languages via DevDocs.io API
- Automatic version discovery (e.g., resolves "ruby" to "ruby~3.4")
- Dual-strategy loading: lightweight HTML files or full database fallback
- Cleans up HTML content by removing compatibility tables and navigation

**SphinxProvider** (`sphinx.py`)
- Parses Sphinx-generated documentation (Pandas, NumPy, Django, etc.)
- Decodes binary `objects.inv` inventory files
- Matches function names using exact, prefix, and substring matching

## Testing

The project includes a comprehensive test suite covering all providers:

```bash
pytest
```

Tests verify:
- Successful documentation retrieval
- Correct parsing of HTML to Markdown
- Cache behavior (both cached and fresh fetches)
- Error handling for non-existent queries

## Technical Implementation

### Caching Strategy
Uses `requests-cache` with SQLite backend, storing responses in `~/.docs_cli/http_cache`. Cache expires after 24 hours. The `--force` flag bypasses cache by deleting specific entries before making requests.

### HTML Parsing
Documentation is parsed using BeautifulSoup (lxml parser) and converted to Markdown using markdownify. Cleanup includes:
- Removal of navigation, sidebars, and advertisements
- Stripping compatibility tables and formal syntax sections
- Filtering out excessive whitespace and horizontal rules

### Error Handling
Providers return a three-tuple: `(url, result, cache_status)`. Failed lookups return `(None, error_message, None)`. Python provider includes suggestion generation using difflib for close matches.

## Design Decisions

1. **Modular Provider System**: Each documentation source has its own provider class implementing a common interface, making it easy to add new sources.

2. **Aggressive Caching**: Documentation doesn't change frequently, so 24-hour cache is reasonable and significantly improves performance.

3. **Fallback Mechanisms**: DevDocs provider tries lightweight HTML files first, then falls back to full database download. C++ provider tries multiple URL patterns.

4. **Clean Terminal Output**: All HTML is converted to Markdown with careful removal of web-specific elements to ensure readable terminal display.

## Requirements

- Python 3.7+
- Libraries: typer, rich, requests, requests-cache, beautifulsoup4, lxml, markdownify

## License

Apache License 2.0