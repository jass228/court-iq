import typer
from src.generate.answer import build_chain

app = typer.Typer(help="CLI to CourtIQ for fiba")

chain = build_chain()


@app.command()
def run_fiba():
    while True:  # chain + model loaded once, before the loop
        question = input("Question: ")
        if question.strip().lower() in {"exit", "quit", ""}:
            break
        print(f"Answer: {chain.invoke(question)}\n{'-' * 50}")
