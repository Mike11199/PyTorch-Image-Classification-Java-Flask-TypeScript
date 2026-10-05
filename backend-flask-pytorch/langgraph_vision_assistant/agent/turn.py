"""Prepare one model turn and translate its outcome into graph state updates.

nodes.py calls these helpers before and after inference. A ModelTurn contains
only the data needed for that call. The returned AssistantState dictionaries
update LangGraph's conversation, attempt counter, and eventual browser reply.
"""

from dataclasses import dataclass
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage

from ..telemetry import log_event
from .prompt import initial_messages
from .state import AssistantState, PlanError

MAX_MODEL_CALLS = 3


@dataclass(frozen=True)
class ModelTurn:
    """Conversation and bookkeeping for one attempt to ask Qwen."""

    messages: list[AnyMessage]
    attempt: int
    request_id: str


def prepare_turn(state: AssistantState) -> ModelTurn:
    """Start the next attempt, refusing to exceed the three-call budget."""
    attempt = state.get('attempt', 0) + 1
    if attempt > MAX_MODEL_CALLS:
        raise PlanError('The model could not complete valid tool calls. Try a shorter request.')
    messages = state.get('messages') or initial_messages(state['context'])
    return ModelTurn(messages, attempt, state['request_id'])


def retry_turn(turn: ModelTurn, error: ValueError) -> AssistantState:
    """Add correction feedback without allowing malformed calls to run."""
    log_event('model_response_invalid', turn.request_id, attempt=turn.attempt, error=str(error))
    return {'messages': turn.messages + [HumanMessage(str(error))],
            'attempt': turn.attempt, 'tool_call_ids': []}


def accept_reply(turn: ModelTurn, response: AIMessage) -> AssistantState:
    """Save valid tool calls, or finish with the model's clarification text."""
    call_ids = [str(call['id']) for call in response.tool_calls]
    update: AssistantState = {
        'messages': turn.messages + [response],
        'attempt': turn.attempt,
        'tool_call_ids': call_ids,
    }
    log_event('tools_requested', turn.request_id, attempt=turn.attempt, calls=response.tool_calls)
    if not call_ids:
        update['result'] = {'actions': [], 'message': str(response.content).strip()}
    return update
