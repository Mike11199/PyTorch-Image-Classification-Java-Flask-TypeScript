"""State passed between the small, named LangGraph workflow steps."""

from typing import TypedDict


class AssistantState(TypedDict, total=False):
    context: dict
    request_id: str
    plan: dict | None
    validation_error: str
    attempt: int
    result: dict
