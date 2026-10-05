"""Describe the data shared by the steps of one assistant request.

The service starts this dictionary with context (user text and viewer settings)
and a request ID. As the graph runs, nodes add conversation messages, an attempt
count, tool-call IDs, and finally result: the reply returned to the browser.

Nodes return partial dictionaries. LangGraph replaces ordinary fields and uses
add_messages to merge conversation entries by message ID. This preserves the
tool feedback needed for another model call. Each HTTP request starts fresh.
"""

from collections.abc import Callable, Sequence
from typing import Annotated, TypeAlias, TypedDict

from langchain_core.messages import AIMessage, AnyMessage
from langchain_core.tools import BaseTool
from langgraph.graph.message import add_messages

from ..types import AssistantResult
from ..viewer.state import ViewerContext

# A model receives conversation, available tools, and a logging ID, then replies.
ModelCall: TypeAlias = Callable[[list[AnyMessage], Sequence[BaseTool], str], AIMessage]


class PlanError(ValueError):
    """The model could not finish valid tool calls within the request budget."""


class AssistantState(TypedDict, total=False):
    """Graph inputs, accumulated chat history, and the final browser response.

    Nodes return only the fields they change. LangGraph merges message updates.
    """

    context: ViewerContext  # User text, detected classes, and current settings.
    request_id: str  # Connects log messages belonging to this HTTP request.
    messages: Annotated[list[AnyMessage], add_messages]  # Conversation with Qwen.
    attempt: int  # Number of model calls made so far (maximum three).
    tool_call_ids: list[str]  # Calls from the latest model turn, in requested order.
    result: AssistantResult  # Present only when a browser reply is ready.
