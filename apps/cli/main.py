import os

os.environ.setdefault("HF_HUB_OFFLINE", "1")  # coupe le warning HF
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")  # coupe "Loading weights"

import typer
from apps.cli.commands import run_ask, run_index

app = typer.Typer(help="RAG Tools")

app.command("index")(run_index)
app.command("ask")(run_ask)

if __name__ == "__main__":
    app()
