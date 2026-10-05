"""Run one assistant request and return its final browser reply.

api/routes.py calls run_assistant with validated text and viewer settings. The
service reserves the single assistant request slot, creates the initial graph
state, and invokes the workflow built by agent/graph.py.

When the workflow finishes, its result contains browser edits or clarification
text. The route formats that result as JSON. The request slot is released even
when inference or validation fails, so a later request can still run.
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
