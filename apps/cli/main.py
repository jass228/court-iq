import typer
from apps.cli.commands.index import run_index

app = typer.Typer(help="RAG Tools")

app.command("index")(run_index)

if __name__ == "__main__":
    app()
