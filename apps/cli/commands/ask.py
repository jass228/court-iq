import readline  # noqa: F401
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from src.generate.answer import answer


console = Console()


def run_ask():
    console.print(
        Panel.fit(
            "🏀 [bold]CourtIQ[/bold] - Basketball rules assistant [dim](FIBA · NBA)[/dim]",
            border_style="cyan",
        )
    )

    while True:
        question = Prompt.ask("\n[bold cyan]Question[/bold cyan]").strip()
        if question.lower() in {"exit", "quit", ""}:
            console.print("[dim]See you soon... 👋[/dim]")
            break
        with console.status("[cyan]Research & writing...", spinner="dots"):
            response = answer(question)
        console.print(
            Panel(
                Markdown(response), title="[green]Answer[/green]", border_style="green"
            )
        )
