"""Perform the assistant's steps before and after tool execution.

ask_qwen sends the conversation to the local model and saves its reply. When
that reply requests tools, graph.py sends it to LangGraph's ToolNode, which calls
the functions in tools/viewer.py. collect_browser_commands then reads their
results and prepares either the browser reply or feedback for another attempt.

Each function receives state, the dictionary shared between steps, and returns
only the fields it changes. graph.py chooses the next step from that updated
state; these functions do not call each other directly.
"""

from langchain_core.messages import HumanMessage

from ..model.validation import validate_model_reply
from ..telemetry import log_event
from .tool_results import FailedToolBatch, browser_commands
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
    except FailedToolBatch as error:
        log_event('tool_batch_failed', state['request_id'], attempt=state['attempt'], error=str(error))
        return {'messages': [HumanMessage(
            'No commands were applied. Correct the tool errors and resend every '
            'requested command together. The user request is: ' + state['context'].message
        )]}

    log_event('tool_batch_completed', state['request_id'], attempt=state['attempt'], action_count=len(commands))
    if not commands:
        return {}
    return {'result': {'actions': commands, 'message': ''}}
