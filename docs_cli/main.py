import typer
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from docs_cli.providers import get_provider

# Initialize console globally
console = Console()

def main(
    language: str = typer.Argument(None, help="Programming language (python, cpp, etc.) or 'info'"),
    query: str = typer.Argument(None, help="Search query (e.g. print, vector)"),
    force: bool = typer.Option(False, "--force", "-f", help="Force refresh data (ignore cache)"),
    anomaly: bool = typer.Option(False, "--anomaly", "-a", help="Force to trigger anomaly badge", hidden=True),
    version: bool = typer.Option(False, "--version", "-v", help="Show version"),
):
    """
    Docs CLI: Search documentation for a specific query.
    Usage: docs [OPTIONS] [LANGUAGE] [QUERY]
    
    Options can be placed anywhere: before, after, or between arguments.
    """
    # 1. Handle version flag
    if version:
        console.print("[bold yellow]Docs CLI Tool[/bold yellow] v0.2 (Alpha)")
        return

    # 2. Handle 'info' command (now as a special argument)
    if language and language.lower() == "info":
        console.print("[bold yellow]Docs CLI Tool[/bold yellow] v0.2 (Alpha)")
        console.print("Created for CS50 Final Project")
        console.print("\nSupported Languages:")
        console.print("  • Python (python, py)")
        console.print("  • C++ (cpp, c++)")
        console.print("  • And many more via DevDocs.io")
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
            "  • [bold]docs --help[/bold] - Show detailed help\n"
            "  • [bold]docs --version[/bold] - Show version",
            title="Welcome to Docs CLI",
            border_style="blue"
        ))
        return

    # 4. Main search logic
    console.print(f"[bold grey50]Searching for '{query}' in {language} docs...[/bold grey50]")

    # Get the appropriate provider based on language
    provider = get_provider(language)

    if not provider:
        console.print(Panel(
            f"[red]Sorry, documentation for '{language}' is not supported yet.[/red]\n"
            f"Supported languages: python, cpp, rust, js, css, html, and more.",
            title="Unsupported Language",
            border_style="red"
        ))
        return

    # Perform the search
    url, result, is_cached = provider.search(query, force_refresh=force, force_anomaly=anomaly)

    if url:
        # Found - Display with source badge
        if is_cached == "anomaly":
            source_badge = "[bold red]ALTERNATIVE DIMENSION[/bold red]"
            border_color = "red"
        elif is_cached is not None:
            source_badge = "[bold yellow]⚡ CACHED[/bold yellow]" if is_cached else "[bold blue]🌐 ONLINE[/bold blue]"
            border_color = "green"
        else:
            source_badge = "[bold grey50]UNKNOWN[/bold grey50]"
            border_color = "green"
        
        console.print(Panel.fit(
            f"[bold green]Found![/bold green]\n\n[link={url}]{url}[/link]",
            title=f"{language.capitalize()}: {query} ({source_badge})",
            border_style=border_color
        ))
        
        # Markdown allows the text to look better
        console.print(Markdown(result))
        console.print("[grey50]" + "-"*50 + "[/grey50]")
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

def run():
    typer.run(main)

app = run

if __name__ == "__main__":
    # Run as a single command (allows flags anywhere in the command line)
    typer.run(main)