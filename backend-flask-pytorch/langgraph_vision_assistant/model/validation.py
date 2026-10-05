"""Check a model reply before allowing its requested tools to run.

ask_qwen in agent/nodes.py calls validate_model_reply after inference. We reject
broken tool-call JSON, missing or duplicate call IDs, excessive calls, and
invalid clarification text. A fresh message ID keeps each attempt separate in
the conversation when LangGraph merges state updates.

Invalid replies raise ValueError so the node can give Qwen correction feedback.
Tool argument values are checked later by Pydantic and tools/checks.py; a reply
passing these format checks does not prove Qwen understood the user.
"""

from uuid import uuid4

from langchain_core.messages import AIMessage, ToolCall

MAX_TOOL_CALLS = 6


def validate_model_reply(response: AIMessage) -> AIMessage:
    """Validate a response and give this conversation turn a fresh message ID."""
    if not isinstance(response, AIMessage) or response.invalid_tool_calls:
        raise ValueError('Return valid tool calls or a short clarification.')
    if response.tool_calls:
        check_tool_calls(response.tool_calls)
    else:
        check_clarification(response.content)
    # LangGraph uses message IDs when merging history. A retry is a new turn.
    return response.model_copy(update={'id': uuid4().hex})


def check_tool_calls(calls: list[ToolCall]) -> None:
    """Require a small set of calls with IDs that can be matched to their results."""
    if len(calls) > MAX_TOOL_CALLS:
        raise ValueError('Use at most six tool calls.')
    seen_ids: set[str] = set()
    for call in calls:
        call_id = call['id']
        if not call_id or call_id in seen_ids:
            raise ValueError('Each tool call needs a unique ID.')
        seen_ids.add(call_id)


def check_clarification(content: object) -> None:
    """Accept a short text reply when Qwen needs clarification instead of tools."""
    if not isinstance(content, str):
        raise ValueError('Return a text clarification.')
    if not 1 <= len(content.strip()) <= 240:
        raise ValueError('Return tool calls or a clarification of 1–240 characters.')
