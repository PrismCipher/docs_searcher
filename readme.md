# Docs CLI Searcher

A blazing fast, offline-capable CLI tool to search developer documentation directly from your terminal. 
Supports **Python**, **C++**, **JavaScript**, **Rust**, **Pandas**, and 50+ other languages and libraries via DevDocs API.

#### Video Demo:  <URL_TO_YOUR_VIDEO>

## Features

* **Instant Answers:** Aggressive caching logic means repeated searches take <10ms.
* **Multi-Provider Architecture:**
    * **Native:** High-quality parsers for Python (docs.python.org) and C++ (cppreference.com).
    * **Sphinx:** Support for Python libraries like Pandas, Django, NumPy via `objects.inv` parsing.
    * **DevDocs:** Universal provider accessing the massive [DevDocs.io](https://devdocs.io) database (Ruby, Go, CSS, HTML, etc.).
* **Beautiful Output:** Syntax highlighting, readable formatting, and elimination of web-clutter (ads, navbars).
* **Smart Pager:** Automatically uses a pager for long documentation content (Linux/Mac) or clean console output (Windows).
* **Fuzzy Search:** Typo in `functools`? The tool will suggest `functools`.

## Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/YOUR_USERNAME/docs_searcher

    cd docs_searcher
    ```

2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3.  (Optional) Install globally (to run `docs` from anywhere):
    ```bash
    pip install -e .
    ```

## Usage

Basic search syntax:
```bash
docs [LANGUAGE] [QUERY]
```

### Examples

**Python (Built-in)**

```bash
docs python print
docs python len
```

**C++ (Standard Library)**

```bash
docs cpp vector
docs cpp std::sort
```

**Web Development (via DevDocs)**

```bash
docs dom console
docs js map
docs css flex
docs html div
```

**Python Libraries (via Sphinx)**

```bash
docs pandas read_csv
docs django Model
docs numpy array
```

**Other Languages (Ruby, Rust, Go...)**

```bash
docs ruby print
docs rust Vec
docs go fmt
```

### Options

  * `--force` / `-f`: Force a fresh network request (ignore cache). Useful if docs are updated or broken.
    ```bash
    docs python print --force
    ```
  * `--help`: Show help message and list of commands.
    ```bash
    docs --help
    ```
  * `--version`: Show current version.

## Project Structure

  * `docs_cli/main.py`: Entry point and CLI interface (Typer + Rich).
  * `docs_cli/providers/`: Modular scrapers logic.
      * `base.py`: Abstract base class for all providers.
      * `python.py`: Official Python docs scraper.
      * `cpp.py`: CppReference scraper.
      * `devdocs.py`: Universal JSON-based scraper for DevDocs.io with auto-version discovery.
      * `sphinx.py`: Binary `objects.inv` parser for Sphinx-based documentation.
  * `tests/`: Unit and integration tests (Pytest).

## Running Tests

This project includes a comprehensive test suite to verify connectivity and parsing logic for all providers.

```bash
pytest
```

## 📝 License

Apache 2.0
