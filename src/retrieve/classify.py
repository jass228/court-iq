from typing import Literal
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from src.generate.llm import get_llm

SYSTEM_PROMPT = """
    You classify basketball questions for a rules assistant.

    - intent = comparison when the user asks to compare leagues.
    - leagues : list every league explicitly mentioned; empty if none.
    - intent = out_of_scope if it's not about basketball rules/tactics.
"""


class QueryClassification(BaseModel):
    """Routing decision for an incoming question."""

    intent: Literal["rule_lookup", "comparison", "tactics", "out_of_scope"] = Field(
        description="The kind of question being asked."
    )
    leagues: list[Literal["fiba", "nba"]] = Field(
        default_factory=list,
        description="Leagues the question targets. Empty means unspecified/all.",
    )


CLASSIFY_PROMPT = ChatPromptTemplate.from_messages(
    [("system", SYSTEM_PROMPT), ("human", "{question}")]
)


def classify_query(question: str) -> QueryClassification:
    """Classify a question into intent + target leagues."""
    classifier = CLASSIFY_PROMPT | get_llm().with_structured_output(QueryClassification)
    return classifier.invoke({"question": question})
