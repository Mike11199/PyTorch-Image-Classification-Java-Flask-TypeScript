"""Choose which assistant step runs next, from a user request to a final reply.

service.py starts this workflow with the user's text and viewer settings.
The normal path for "make cats red" is:

    ask_qwen                 Qwen requests the set_class_color tool.
        |
    run_tools                ToolNode calls the Python tool in tools/viewer.py.
        |
    collect_browser_commands Collect the edit it prepared (tools/results.py).
        |
    END                      Return the edit to the service, then the browser.

There are two decisions, implemented by the functions below build_workflow:
    after_qwen: run requested tools, finish a text reply, or retry invalid output.
    after_tools: finish with edits, or ask Qwen again using tool feedback.
Retries stop after three model calls; agent/turn.py enforces that limit.

LangGraph calls each step a "node" and each connection an "edge". State is the
dictionary passed between steps. build_workflow registers the steps and their
connections, then compile() creates the object that service.py can invoke.
The step functions themselves live in nodes.py; ToolNode comes from LangGraph.
"""

from functools import partial

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode

from ..model.client import call_model
from ..tools.results import tool_error
from ..tools.registry import VIEWER_TOOLS
from .nodes import ask_qwen, collect_browser_commands
from .state import AssistantState, ModelCall, PlanError

WORKFLOW_RECURSION_LIMIT = 16


def build_workflow(model: ModelCall = call_model) -> CompiledStateGraph:
    """Register the three steps, connect them, and return a runnable workflow.

    partial supplies the model dependency to ask_qwen; LangGraph supplies state
    when the step runs. Tests can supply a model without replacing the tools.
    """
    graph = StateGraph(AssistantState)

    graph.add_node('ask_qwen', partial(ask_qwen, model=model))
    graph.add_node('run_tools', ToolNode(VIEWER_TOOLS, handle_tool_errors=tool_error))
    graph.add_node('collect_browser_commands', collect_browser_commands)

    graph.add_edge(START, 'ask_qwen')
    graph.add_conditional_edges('ask_qwen', after_qwen, ['run_tools', 'ask_qwen', END])
    graph.add_edge('run_tools', 'collect_browser_commands')
    graph.add_conditional_edges('collect_browser_commands', after_tools, ['ask_qwen', END])
    return graph.compile()


def after_qwen(state: AssistantState) -> str:
    """Run requested tools, finish a clarification, or retry malformed output."""
    if 'result' in state:
        return END
    if state['tool_call_ids']:
        return 'run_tools'
    return 'ask_qwen'


def after_tools(state: AssistantState) -> str:
    """Finish if browser commands are ready; otherwise let Qwen use tool feedback."""
    if 'result' in state:
        return END
    return 'ask_qwen'
