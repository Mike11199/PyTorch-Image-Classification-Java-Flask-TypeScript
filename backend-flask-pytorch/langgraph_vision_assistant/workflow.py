"""Build the bounded generate/validate/repair LangGraph workflow."""

from functools import partial

from langgraph.graph import END, START, StateGraph

from .qwen import generate_plan
from .styles import normalize_explicit_styles
from .telemetry import log_event
from .tools import validate_plan
from .workflow_state import AssistantState


class PlanError(ValueError):
    pass


def generate_node(state: AssistantState, generate) -> dict:
    """Ask Qwen for a plan and normalize explicit styling instructions."""
    try:
        attempt = state.get('attempt', 0) + 1
        plan = generate(
            state['context'], state.get('validation_error', ''), state['request_id']
        )
        plan = normalize_explicit_styles(plan, state['context'])
    except ValueError:
        plan = None
    log_event('plan_normalized', state['request_id'], attempt=attempt, plan=plan)
    return {'plan': plan, 'attempt': attempt}


def validate_node(state: AssistantState) -> dict:
    """Convert the generated plan into a safe, executable viewer result."""
    try:
        result = validate_plan(state['plan'], state['context'])
        log_event(
            'plan_validated', state['request_id'], attempt=state['attempt'],
            action_count=len(result['actions']),
        )
        return {'result': result, 'validation_error': ''}
    except ValueError as error:
        log_event(
            'validation_failed', state['request_id'], attempt=state['attempt'],
            error=str(error),
        )
        return {'validation_error': str(error)}


def route_after_validation(state: AssistantState):
    """Retry an invalid plan twice, then stop without partial actions."""
    if not state['validation_error']:
        return END
    if state['attempt'] < 3:
        return 'generate'
    raise PlanError('The model could not form a valid action plan. Try a shorter request.')


def build_workflow(generate=generate_plan):
    graph = StateGraph(AssistantState)
    graph.add_node('generate', partial(generate_node, generate=generate))
    graph.add_node('validate', validate_node)
    graph.add_edge(START, 'generate')
    graph.add_edge('generate', 'validate')
    graph.add_conditional_edges(
        'validate', route_after_validation, {'generate': 'generate', END: END}
    )
    return graph.compile()
