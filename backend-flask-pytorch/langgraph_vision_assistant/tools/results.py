"""Turn completed tool results into the edits sent to the browser.

After ToolNode runs the requested functions, collect_browser_commands in
agent/nodes.py calls browser_commands here. Its inputs are the conversation and
the IDs of the tools just requested. Each ToolMessage holds feedback for Qwen
in content and an optional list of browser edits in artifact.

We select the latest results, match their request order, reject the whole set
if any tool failed, and return the edit dictionaries. Information-only tools
have no edit. The caller decides whether to finish or ask Qwen again; the
browser applies the returned edits after receiving the HTTP reply.
"""

from langchain_core.messages import AnyMessage, ToolMessage

from ..types import ViewerCommand


class FailedToolBatch(ValueError):
    """At least one tool failed, so none of this set of commands can be applied."""


def browser_commands(messages: list[AnyMessage], call_ids: list[str]) -> list[ViewerCommand]:
    """Return this attempt's edits, or raise FailedToolBatch if any tool failed.

    messages includes the completed tool results; call_ids gives their request
    order. An empty list means the tools prepared no browser edits."""
    results = latest_tool_results(messages, len(call_ids))
    ordered_results = in_call_order(results, call_ids)
    require_success(ordered_results)
    return extract_commands(ordered_results)


def latest_tool_results(messages: list[AnyMessage], count: int) -> list[ToolMessage]:
    """Take the last count messages, excluding results from earlier attempts."""
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
    """Match results to call IDs so later edits still override earlier ones."""
    by_id = {result.tool_call_id: result for result in results}
    if len(by_id) != len(results) or set(by_id) != set(call_ids):
        raise RuntimeError('Tool results do not match the requested calls.')
    return [by_id[call_id] for call_id in call_ids]


def require_success(results: list[ToolMessage]) -> None:
    """Reject every edit if one failed, so a request is never partly applied."""
    for result in results:
        if result.status == 'error':
            raise FailedToolBatch(str(result.content))


def extract_commands(results: list[ToolMessage]) -> list[ViewerCommand]:
    """Combine each tool's edits; skip information-only results."""
    commands: list[ViewerCommand] = []
    for result in results:
        if result.artifact is not None:
            commands.extend(result.artifact)
    return commands


def tool_error(error: ValueError) -> str:
    """Return a bounded validation message for Qwen to use when correcting a call."""
    return str(error)[:600]
