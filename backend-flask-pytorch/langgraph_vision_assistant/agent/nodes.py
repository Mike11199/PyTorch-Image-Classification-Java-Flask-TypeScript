"""Ask Qwen what to do, then prepare the browser reply after its tools finish.

graph.py runs these steps in this order:

    ask_qwen -> LangGraph's ToolNode -> collect_browser_commands

For "make cats red", ask_qwen saves Qwen's request to call set_class_color.
ToolNode calls that Python function from tools/viewer.py and saves its result.
collect_browser_commands uses tools/results.py to extract the prepared edit,
then returns {'result': {'actions': [the edit], 'message': ''}}.
The service reads that result and the HTTP route sends it to the browser.

These functions are called "nodes" because they are steps in the graph.
Each receives state: a dictionary containing this request's conversation and
progress. Each returns the fields LangGraph should update. Message updates
are merged into the conversation; omitted fields keep their existing values.

If tools fail or only return information, there is no final result yet.
graph.py sends the updated conversation back to ask_qwen for another attempt.
"""

from langchain_core.messages import HumanMessage

from ..model.validation import validate_model_reply
from ..telemetry import log_event
from ..tools.results import FailedToolBatch, browser_commands
from ..tools.registry import VIEWER_TOOLS
from .turn import prepare_turn, retry_turn, accept_reply
from .state import AssistantState, ModelCall, PlanError


def ask_qwen(state: AssistantState, model: ModelCall) -> AssistantState:
    """Ask for tool calls or a clarification, including any previous tool errors.

    Invalid output becomes feedback for the next attempt. No tool runs until
    the model response passes its format checks. Three attempts is the limit.
    """
    turn = prepare_turn(state)
    try:
        response = model(turn.messages, VIEWER_TOOLS, turn.request_id)
        response = validate_model_reply(response)
    except PlanError:
        raise
    except ValueError as error:
        return retry_turn(turn, error)
    return accept_reply(turn, response)


def collect_browser_commands(state: AssistantState) -> AssistantState:
    """Prepare the browser reply after ToolNode has finished this set of calls.

    A failed call discards every command in the set and asks Qwen to retry.
    A read-only tool produces no command, so Qwen gets another turn to use its
    result. Successful commands finish the request without another model call.
    """
    try:
        commands = browser_commands(state['messages'], state['tool_call_ids'])
    except FailedToolBatch:
        log_event('tool_batch_failed', state['request_id'], attempt=state['attempt'])
        return {'messages': [HumanMessage(
            'No commands were applied. Correct the tool errors and resend every '
            'requested command together.'
        )]}

    log_event('tool_batch_completed', state['request_id'], attempt=state['attempt'], action_count=len(commands))
    if not commands:
        return {}
    return {'result': {'actions': commands, 'message': ''}}
