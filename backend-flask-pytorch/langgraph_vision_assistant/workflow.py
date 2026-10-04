"""Build the bounded plan/style-rules/validate/repair LangGraph workflow."""

from functools import partial

from langgraph.graph import END, START, StateGraph

from .qwen import generate_plan
from .styles import apply_explicit_style_requests
from .telemetry import log_event
from .tools import validate_plan
from .workflow_state import AssistantState

WORKFLOW_RECURSION_LIMIT = 12


class PlanError(ValueError):
    """Raised after Qwen produces three plans that fail validation."""

    pass


def generate_node(state: AssistantState, generate) -> dict:
    """Ask Qwen for a proposed viewer-action plan."""
    attempt = state.get('attempt', 0) + 1
    try:
        plan = generate(
            state['context'], state.get('validation_error', ''), state['request_id']
        )
    except ValueError:
        plan = None
    log_event('plan_generated', state['request_id'], attempt=attempt, plan=plan)
    return {'plan': plan, 'attempt': attempt}


def apply_explicit_styles_node(state: AssistantState) -> dict:
    """Make Qwen's plan obey colors and box/mask targets stated by the user."""
    plan = apply_explicit_style_requests(state['plan'], state['context'])
    log_event(
        'explicit_styles_applied', state['request_id'],
        attempt=state['attempt'], plan=plan,
    )
    return {'plan': plan}


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
    """Compile the graph, injecting a fake planner in tests when requested."""
    graph = StateGraph(AssistantState)
    graph.add_node('generate', partial(generate_node, generate=generate))
    graph.add_node('apply_explicit_styles', apply_explicit_styles_node)
    graph.add_node('validate', validate_node)
    graph.add_edge(START, 'generate')
    graph.add_edge('generate', 'apply_explicit_styles')
    graph.add_edge('apply_explicit_styles', 'validate')
    graph.add_conditional_edges(
        'validate', route_after_validation, {'generate': 'generate', END: END}
    )
    return graph.compile()
