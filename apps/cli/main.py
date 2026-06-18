import typer
from apps.cli.commands.index import run_index
from apps.cli.commands.try_fiba import run_fiba

app = typer.Typer(help="RAG Tools")

app.command("index")(run_index)
app.command("fiba")(run_fiba)

if __name__ == "__main__":
    app()
