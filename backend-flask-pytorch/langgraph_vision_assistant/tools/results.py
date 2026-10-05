"""Collect the browser edits prepared by the tools that just finished.

Example: the user asks "make cats red" on the mask page.

1. Qwen requests set_class_color(cat, #ff0000, both), with a call ID.
2. LangGraph runs that function in tools/viewer.py. The function prepares a
   dictionary describing the edit. It has not changed the displayed image yet.
3. LangGraph wraps the function's output in a ToolMessage:
       tool_call_id = the ID from step 1
       status       = 'success' or 'error'
       content      = text Qwen can read
       artifact     = {'type': 'set_class_color', 'className': 'cat',
                       'color': '#ff0000', 'target': 'both'}
   "Artifact" is LangChain's name for extra data attached to a tool result.
   In this application, that data is the browser edit dictionary.
4. collect_browser_commands in agent/nodes.py calls browser_commands below.
   We extract the edit dictionaries and return them as a list.
5. The node puts that list in the HTTP reply's 'actions' field. The browser
   receives the reply and applies the edits.

Start reading at browser_commands. Its four helpers select this attempt's
results, restore request order, check for failures, and extract the edits.
Old results stay in the conversation for Qwen, but are never applied again.

If any tool failed, we raise FailedToolBatch. The caller asks Qwen to correct
the whole attempt; none of its edits are sent. If tools only read information,
their artifacts are None, so we return an empty list and Qwen gets another turn.
"""

from langchain_core.messages import AnyMessage, ToolMessage

from ..types import ViewerCommand


class FailedToolBatch(ValueError):
    """At least one tool failed, so none of this set of commands can be applied."""


def browser_commands(messages: list[AnyMessage], call_ids: list[str]) -> list[ViewerCommand]:
    """Return edits from the latest tool calls, or raise FailedToolBatch.

    messages is the conversation after ToolNode has appended its results.
    call_ids lists the calls Qwen requested in this attempt, in request order.
    An empty return value means these tools prepared no browser edits.
    """
    results = latest_tool_results(messages, len(call_ids))
    ordered_results = in_call_order(results, call_ids)
    require_success(ordered_results)
    return extract_commands(ordered_results)


def latest_tool_results(messages: list[AnyMessage], count: int) -> list[ToolMessage]:
    """Take the last count messages: one result per tool that just ran.

    Earlier messages may contain edits from a failed attempt. Selecting only
    this final group prevents those old edits from reaching the browser.
    """
    if count == 0:
        return []
    if len(messages) < count:
        raise RuntimeError('Missing tool results.')
    # ToolNode appends one result per call to the end of message history.
    results: list[ToolMessage] = []
    for message in messages[-count:]:
        if not isinstance(message, ToolMessage):
            raise RuntimeError('Expected a result for every tool call.')
        results.append(message)
    return results


def in_call_order(results: list[ToolMessage], call_ids: list[str]) -> list[ToolMessage]:
    """Put results in Qwen's call order, even if tools finished out of order.

    Order matters when two commands change the same setting: the later edit
    should win. Missing, duplicate, or unexpected results are internal errors.
    """
    by_id = {result.tool_call_id: result for result in results}
    if len(by_id) != len(results) or set(by_id) != set(call_ids):
        raise RuntimeError('Tool results do not match the requested calls.')
    return [by_id[call_id] for call_id in call_ids]


def require_success(results: list[ToolMessage]) -> None:
    """Raise if any result failed, before the caller can return any edits.

    For 'cats red and dogs blue', a failed dog edit also withholds the cat edit.
    The next model turn must provide the complete corrected set.
    """
    for result in results:
        if result.status == 'error':
            raise FailedToolBatch()


def extract_commands(results: list[ToolMessage]) -> list[ViewerCommand]:
    """Take each result's edit dictionary, stored in its artifact field.

    get_viewer_context only returns information to Qwen. Its artifact is None,
    so it contributes no browser edit. The caller checks success beforehand.
    """
    commands: list[ViewerCommand] = []
    for result in results:
        if result.artifact is not None:
            commands.append(result.artifact)
    return commands


def tool_error(error: ValueError) -> str:
    """Return a bounded validation message for Qwen to use when correcting a call."""
    return str(error)[:600]
