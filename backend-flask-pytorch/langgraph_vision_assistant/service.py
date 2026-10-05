"""Application entry point: coordinate one assistant request.

The HTTP layer calls run_assistant with validated data. This service reserves a
request slot, runs the graph, and always releases the slot. It knows nothing about
Flask responses, color interpretation, or model process startup.

Read agent/graph.py next to see how the assistant runs.
"""

import threading

from langchain_core.runnables import RunnableConfig

from .agent.graph import WORKFLOW_RECURSION_LIMIT, build_workflow
from .agent.state import AssistantState
from .telemetry import log_event
from .types import AssistantResult, ViewerContext

workflow = build_workflow()
_request_slot = threading.BoundedSemaphore(1)


class AssistantBusyError(TimeoutError):
    """Another assistant request already owns the single request slot."""


def run_assistant(context: ViewerContext, request_id: str) -> AssistantResult:
    """Run the agent once; fail promptly when busy and release the slot on any error."""
    log_event('request_started', request_id, page=context['page'],
              message=context['message'][:200], available_class_count=len(context['availableClasses']))
    if not _request_slot.acquire(blocking=False):
        raise AssistantBusyError('The assistant is busy. Please try again shortly.')
    try:
        state: AssistantState = {'context': context, 'request_id': request_id}
        config: RunnableConfig = {'recursion_limit': WORKFLOW_RECURSION_LIMIT}
        return workflow.invoke(state, config)['result']
    finally:
        _request_slot.release()
