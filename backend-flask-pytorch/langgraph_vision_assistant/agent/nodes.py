"""Graph steps: ask the model, collect a tool batch, and bound retries."""

from uuid import uuid4

from langchain_core.messages import AIMessage, ToolMessage, HumanMessage
from langgraph.graph import END
from langgraph.prebuilt import tools_condition

from ..telemetry import log_event
from ..tools.viewer import VIEWER_TOOLS
from .prompt import initial_messages
from .state import AssistantState, ModelCall, PlanError

MAX_MODEL_CALLS = 3
MAX_TOOL_CALLS = 6


def validate_response(response: AIMessage) -> None:
    """Reject malformed batches before any tool runs; do not reinterpret language."""
    if not isinstance(response, AIMessage) or response.invalid_tool_calls:
        raise ValueError('Return valid tool calls or a short clarification.')
    if len(response.tool_calls) > MAX_TOOL_CALLS:
        raise ValueError('Use at most six tool calls.')
    seen_ids: set[str] = set()
    for call in response.tool_calls:
        call_id = call['id']
        if not call_id or call_id in seen_ids:
            raise ValueError('Each tool call needs a unique ID.')
        seen_ids.add(call_id)
    if not response.tool_calls:
        if not isinstance(response.content, str) or not 1 <= len(response.content.strip()) <= 240:
            raise ValueError('Return tool calls or a clarification of 1–240 characters.')


def model_node(state: AssistantState, model: ModelCall) -> AssistantState:
    """Ask Qwen for the next batch, keeping tool results in its message history."""
    messages = state.get('messages') or initial_messages(state['context'])
    attempt = state.get('attempt', 0) + 1
    try:
        response = model(messages, VIEWER_TOOLS, state['context'], state['request_id'])
        validate_response(response)
    except PlanError:
        raise
    except ValueError as error:
        log_event('model_response_invalid', state['request_id'], attempt=attempt, error=str(error))
        return {'messages': messages + [HumanMessage(str(error))], 'attempt': attempt, 'retry': True}

    # Fresh IDs prevent repeated completions from replacing an earlier turn.
    response = response.model_copy(update={'id': uuid4().hex})
    log_event('tools_requested', state['request_id'], attempt=attempt, calls=response.tool_calls)
    update: AssistantState = {'messages': messages + [response], 'attempt': attempt, 'retry': False}
    if not response.tool_calls:
        update['result'] = {'actions': [], 'message': str(response.content).strip()}
    return update


def current_batch(state: AssistantState) -> list[ToolMessage]:
    """Restore model call order, ignoring results from any earlier attempt."""
    results: dict[str, ToolMessage] = {}
    for message in reversed(state['messages']):
        if isinstance(message, ToolMessage):
            results[message.tool_call_id] = message
        elif isinstance(message, AIMessage):
            ordered = []
            for call in message.tool_calls:
                assert call['id'] is not None  # Checked before ToolNode runs.
                ordered.append(results[call['id']])
            return ordered
    raise RuntimeError('Tool results arrived without a model request.')


def collect_results(state: AssistantState) -> AssistantState:
    """Return every command in a successful batch, or retry without applying any."""
    results = current_batch(state)
    if any(result.status == 'error' for result in results):
        log_event('tool_batch_failed', state['request_id'], attempt=state['attempt'])
        return {'retry': True, 'messages': [HumanMessage(
            'No commands from that batch were applied. Use the tool errors to correct the '
            'request, and resend every requested command as one complete batch.'
        )]}

    actions = [result.artifact for result in results if result.artifact is not None]
    log_event('tool_batch_completed', state['request_id'], attempt=state['attempt'], action_count=len(actions))
    if not actions:
        return {'retry': True}
    return {'retry': False, 'result': {'actions': actions, 'message': ''}}


def retry_or_fail(state: AssistantState) -> str:
    """Count read turns and error repairs against the same three-call budget."""
    if state['attempt'] >= MAX_MODEL_CALLS:
        raise PlanError('The model could not complete valid tool calls. Try a shorter request.')
    return 'model'


def route_after_model(state: AssistantState) -> str:
    """Send valid calls to ToolNode, finish clarifications, or retry bad output."""
    if state['retry']:
        return retry_or_fail(state)
    return tools_condition(state['messages'])


def route_after_tools(state: AssistantState) -> str:
    """Read-only batches and errors need another model turn; commands finish."""
    if state['retry']:
        return retry_or_fail(state)
    return END


def tool_error(error: ValueError) -> str:
    """Give Qwen a bounded argument-validation error to repair."""
    return str(error)[:600]
