"""Define the order of steps for one assistant request.

A LangGraph graph connects Python functions called nodes. Here the path is
ask_qwen -> run_tools -> collect_browser_commands. service.py starts it with
the user's text and viewer settings; nodes.py implements our two custom steps.

The routing functions below decide whether to finish or ask Qwen again. Tool
errors and information-only results return to Qwen; ready edits or clarification
text finish the request. build_workflow compiles these connections into the
workflow object that the service calls.
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
