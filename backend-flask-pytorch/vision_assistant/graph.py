"""A bounded LangGraph: generate -> validate -> one repair or respond."""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from .schemas import validate_plan
from .style_normalization import normalize_explicit_styles


class PlanError(ValueError):
    pass


class State(TypedDict, total=False):
    context: dict
    plan: dict
    error: str
    attempts: int
    result: dict


def build_graph(generate):
    def interpret(state):
        try:
            plan = generate(state['context'], state.get('error', ''))
            plan = normalize_explicit_styles(plan, state['context'])
        except ValueError:
            plan = None
        return {'plan': plan, 'attempts': state.get('attempts', 0) + 1}

    def validate(state):
        try:
            return {'result': validate_plan(state['plan'], state['context']), 'error': ''}
        except ValueError as error:
            return {'error': str(error)}

    def route(state):
        if not state['error']:
            return END
        if state['attempts'] < 3:
            return 'interpret'
        raise PlanError('The model could not form a valid action plan. Try a shorter request.')

    graph = StateGraph(State)
    graph.add_node('interpret', interpret)
    graph.add_node('validate', validate)
    graph.add_edge(START, 'interpret')
    graph.add_edge('interpret', 'validate')
    graph.add_conditional_edges('validate', route, {'interpret': 'interpret', END: END})
    return graph.compile()
