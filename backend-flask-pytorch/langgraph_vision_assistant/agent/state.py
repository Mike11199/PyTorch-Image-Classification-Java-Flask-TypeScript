"""Typed state carried through one assistant request, never shared between users."""

from collections.abc import Callable, Sequence
from typing import Annotated, TypeAlias, TypedDict

from langchain_core.messages import AIMessage, AnyMessage
from langchain_core.tools import BaseTool
from langgraph.graph.message import add_messages

from ..types import AssistantResult, ViewerContext

ModelCall: TypeAlias = Callable[[list[AnyMessage], Sequence[BaseTool], ViewerContext, str], AIMessage]


class PlanError(ValueError):
    """The model could not finish valid tool calls within the request budget."""


class AssistantState(TypedDict, total=False):
    """Graph inputs, accumulated chat history, and the final browser response.

    Nodes return only the fields they change. LangGraph merges message updates.
    """

    messages: Annotated[list[AnyMessage], add_messages]
    context: ViewerContext
    request_id: str
    attempt: int
    retry: bool
    result: AssistantResult
