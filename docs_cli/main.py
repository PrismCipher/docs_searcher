"""
Docs CLI - Search programming documentation from the command line.
"""
import typer
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from . import utils
from .utils import VERSION

# Initialize console globally
console = Console()


def main(
    language: str = typer.Argument(None, help="Programming language (python, cpp, etc.) or 'info'"),
    query: str = typer.Argument(None, help="Search query (e.g. print, vector)"),
    force: bool = typer.Option(False, "--force", "-f", help="Force refresh data (ignore cache)"),
    pager: bool = typer.Option(False, "--pager", "-p", help="Use pager for long output (may break Unicode on Windows)"),
    devdocs: bool = typer.Option(False, "--devdocs", "-d", help="Force use DevDocs.io provider"),
    utf8: bool = typer.Option(False, "--utf8", "-8", help="Force UTF-8 encoding"),
    auto_detect: bool = typer.Option(False, "--auto-detect", "-a", help="Auto-detect encoding from response"),
    version: bool = typer.Option(False, "--version", "-v", help="Show version"),
):
    """
    Docs CLI: Search documentation for a specific query.
    Usage: docs [OPTIONS] [LANGUAGE] [QUERY]
    """
    # 1. Handle version flag
    if version:
        console.print(f"[bold yellow]Docs CLI Tool[/bold yellow] v{VERSION}")
        return

    # 2. Handle 'info' command (now as a special argument)
    if language and language.lower() == "info":
        console.print(f"[bold yellow]Docs CLI Tool[/bold yellow] v{VERSION}")
        console.print("Created for CS50 Final Project")
        console.print("\nSupported Languages:")
        console.print("  • Python (python, py)")
        console.print("  • C++ (cpp, c++)")
        console.print("  • And many more via DevDocs.io (js, rust, css, html...)")
        return

    # 3. If no arguments provided - show welcome panel
    if not language or not query:
        console.print(Panel(
            "Usage: [bold cyan]docs <language> <query> [options][/bold cyan]\n"
            "Example: [bold green]docs python print[/bold green]\n"
            "Example: [bold green]docs cpp vector --force[/bold green]\n"
            "Example: [bold green]docs --force css flex[/bold green]\n\n"
            "Commands:\n"
            "  • [bold]docs info[/bold] - Show tool information\n"
            "  • [bold]docs --help[/bold] - Show detailed help",
            title="Welcome to Docs CLI",
            border_style="blue"
        ))
        return

    # 4. Apply encoding flags
    if utf8:
        utils.DEFAULT_ENCODING = "utf-8"
        utils.AUTO_DETECT_ENCODING = False
    elif auto_detect:
        utils.AUTO_DETECT_ENCODING = True

    # 5. Main search logic
    console.print(f"[bold grey50]Searching for '{query}' in {language} docs...[/bold grey50]")

    from docs_cli.providers import get_provider
    from docs_cli.providers.devdocs import DevDocsProvider

    # Get the appropriate provider based on language
    if devdocs:
        # Force DevDocs.io provider
        provider = DevDocsProvider(language)
    else:
        provider = get_provider(language)

    if not provider:
        console.print(Panel(
            f"[red]Sorry, documentation for '{language}' is not supported yet.[/red]\n",
            title="Unsupported Language",
            border_style="red"
        ))
        return

    # Perform the search
    url, result, is_cached = provider.search(query, force_refresh=force)

    if url:
        # Found - Display with source badge
        if is_cached is True:
            source_badge = "[bold yellow]⚡ CACHED[/bold yellow]"
        elif is_cached is False:
            source_badge = "[bold blue]🌐 ONLINE[/bold blue]"
        else:
            source_badge = "[bold grey50]UNKNOWN[/bold grey50]"

        # Helper function to print the result
        def print_result():
            console.print(Panel.fit(
                f"[bold green]Found![/bold green]\n\n[link={url}]{url}[/link]",
                title=f"{language.capitalize()}: {query} ({source_badge})",
                border_style="green"
            ))

            # Markdown allows the text to look better
            console.print(Markdown(result))
            console.print("[grey50]" + "-" * 50 + "[/grey50]")

        # Use pager if requested (may break Unicode on Windows)
        if pager:
            with console.pager(styles=True):
                print_result()
        else:
            print_result()
    else:
        # Not found - Handle errors and suggestions
        if isinstance(result, dict) and result.get("type") == "did_you_mean":
            # Show suggestions with proper command format
            suggestions = result["matches"]
            suggestion_text = "\n".join([f"  • [bold cyan]docs {language} {match}[/bold cyan]" for match in suggestions])
            
            console.print(Panel(
                f"[yellow]Could not find '{query}'. Did you mean?[/yellow]\n\n{suggestion_text}",
                title="Suggestions",
                border_style="yellow"
            ))
        else:
            # Show error message
            console.print(Panel(
                f"[red]Could not find '{query}' in {language} documentation.[/red]\n\nDetails: {result}",
                title="Error",
                border_style="red"
            ))

# FIX: Bridge typer.run() with setup.py entry point
def run():
    typer.run(main)

app = run

if __name__ == "__main__":
    # Run as a single command (allows flags anywhere in the command line)
    typer.run(main)