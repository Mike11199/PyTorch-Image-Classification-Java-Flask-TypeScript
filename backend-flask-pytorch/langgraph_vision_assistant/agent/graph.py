"""Build the assistant graph. Start here to see the complete request flow.

model -> tools -> collect -> finish
  ^                 |
  +-- read/error ---+
"""

from functools import partial

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode

from ..model.client import call_model
from ..tools.viewer import VIEWER_TOOLS
from .nodes import collect_results, model_node, route_after_model, route_after_tools, tool_error
from .state import AssistantState, ModelCall, PlanError

WORKFLOW_RECURSION_LIMIT = 16


def build_workflow(model: ModelCall = call_model) -> CompiledStateGraph:
    """Connect model inference, registered tools, and atomic command collection.

    Tests inject model responses here; tool execution and routing stay real.
    """
    graph = StateGraph(AssistantState)
    graph.add_node('model', partial(model_node, model=model))
    graph.add_node('tools', ToolNode(VIEWER_TOOLS, handle_tool_errors=tool_error))
    graph.add_node('collect', collect_results)
    graph.add_edge(START, 'model')
    graph.add_conditional_edges('model', route_after_model, {'model': 'model', 'tools': 'tools', END: END})
    graph.add_edge('tools', 'collect')
    graph.add_conditional_edges('collect', route_after_tools, {'model': 'model', END: END})
    return graph.compile()
