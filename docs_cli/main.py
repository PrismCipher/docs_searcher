import typer
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from docs_cli.providers import get_provider

app = typer.Typer()
console = Console()

@app.command()
def search(
    query: str, 
    language: str = typer.Option("python", "--lang", "-l", help="Language doc to search"),
    force: bool = typer.Option(False, "--force", "-f", help="Force refresh data (ignore cache)")
):
    """
    Search documentation for a specific query.
    Usage Example: docs search print
    """
    # Begin response
    console.print(f"[bold grey50]Searching for '{query}' in {language} docs...[/bold grey50]")

    # Get the appropriate provider based on language
    provider = get_provider(language)

    if not provider:
        console.print(Panel(
            f"[red]Sorry, documentation for '{language}' is not supported yet.[/red]\n"
            f"Supported languages: python",
            title="Unsupported Language",
            border_style="red"
        ))
        return

    # Use the provider to search
    url, result, is_cached = provider.search(query, force_refresh=force) # Function from scraper.py

    if url:
        # Found
        # Display with source badge
        if is_cached is not None:
            source_badge = "[bold yellow]⚡ CACHED[/bold yellow]" if is_cached else "[bold blue]🌐 ONLINE[/bold blue]"
        else:
            source_badge = "[bold grey50]UNKNOWN[/bold grey50]"
        
        console.print(Panel.fit(
            f"[bold green]Found![/bold green]\n\n[link={url}]{url}[/link]",
            title=f"{language.capitalize()}: {query} ({source_badge})",
            border_style="green"
        ))
        
        # Markdown allows the text to look better
        console.print(Markdown(result))
        console.print("[grey50]" + "-"*50 + "[/grey50]")
    else:
        # Not found
        # Check for suggestions
        if isinstance(result, dict) and result.get("type") == "did_you_mean":
            suggestions = result["matches"]
            suggestion_text = "\n".join([f"* [bold cyan]{match}[/bold cyan]" for match in suggestions])
            
            console.print(Panel(
                f"[yellow]Could not find '{query}'. Did you mean?[/yellow]\n\n{suggestion_text}",
                title="Suggestions",
                border_style="yellow"
            ))
        # No suggestions
        else:
            console.print(Panel(
                f"[red]Could not find '{query}' in docs.[/red]\nDetails: {result}",
                title="Error",
                border_style="red"
            ))

@app.command()
def info():
    """
    Show info about the tool.
    """
    console.print("[bold yellow]Docs CLI Tool[/bold yellow] v0.1")
    console.print("Created for CS50 Final Project")

if __name__ == "__main__":
    app()