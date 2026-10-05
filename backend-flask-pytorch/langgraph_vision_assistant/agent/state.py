"""The data LangGraph passes from one step to the next during a request.

State is an ordinary dictionary with named fields, not a separate service.
Each node returns a dictionary containing only the fields it wants to update.
Most fields are replaced. messages uses add_messages so new chat messages are
added to the conversation, preserving the tool results Qwen needs on later turns.

The service initially supplies context and request_id. ask_qwen fills in the
conversation and call IDs. A completed request has result, which the service
returns to the browser. A fresh state is created for every HTTP request.
"""

from collections.abc import Callable, Sequence
from typing import Annotated, TypeAlias, TypedDict

from langchain_core.messages import AIMessage, AnyMessage
from langchain_core.tools import BaseTool
from langgraph.graph.message import add_messages

from ..types import AssistantResult, ViewerContext

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
