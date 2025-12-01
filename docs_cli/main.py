import typer
from rich.console import Console
from rich.panel import Panel

# App initialization
app = typer.Typer()
console = Console()

@app.command()
def search(query: str, language: str = typer.Option("python", "--lang", "-l", help="Language doc to search")):
    """
    Search documentation for a specific query.
    """
    # DEVELOPMENT: This is a placeholder for future documentation search logic.
    console.print(Panel.fit(f"[bold green]Searching docs for:[/bold green] [cyan]{query}[/cyan]", title="Docs Searcher"))

    if language.lower() == "python":
        console.print(f"🕵️  Looking into [bold blue]Python[/bold blue] documentation...")  # noqa: F541
        # DEVELOPMENT: Parsing logic will be added here later
    else:
        console.print(f"🕵️  Looking into [bold orange1]{language}[/bold orange1] documentation...")

@app.command()
def info():
    """
    Show info about the tool.
    """
    console.print("[bold yellow]Docs CLI Tool[/bold yellow] v0.1")
    console.print("Created for CS50 Final Project")

if __name__ == "__main__":
    app()