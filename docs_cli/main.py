import typer
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from docs_cli.scraper import get_python_builtin

app = typer.Typer()
console = Console()

@app.command()
def search(query: str, language: str = typer.Option("python", "--lang", "-l", help="Language doc to search")):
    """
    Search documentation for a specific query.
    Usage Example: docs search print
    """
    # Begin response
    console.print(f"[bold grey50]Searching for '{query}' in {language} docs...[/bold grey50]")

    if language.lower() == "python":
        url, result = get_python_builtin(query) # Function from scraper.py

        if url:
            # Found
            console.print(Panel.fit(
                f"[bold green]Found![/bold green]\n\n[link={url}]{url}[/link]",
                title=f"Python: {query}",
                border_style="green"
            ))
            # Markdown allows the text to look better
            
            console.print(Markdown(result))
            
            console.print("[grey50]" + "-"*50 + "[/grey50]")
        else:
            # Not found
            console.print(Panel(
                f"[red]Could not find '{query}' in Python built-in functions.[/red]\nDetails: {result}",
                title="Error",
                border_style="red"
            ))

    else:
        console.print(f"[yellow]Sorry, support for {language} is coming soon![/yellow]")

@app.command()
def info():
    """
    Show info about the tool.
    """
    console.print("[bold yellow]Docs CLI Tool[/bold yellow] v0.1")
    console.print("Created for CS50 Final Project")

if __name__ == "__main__":
    app()