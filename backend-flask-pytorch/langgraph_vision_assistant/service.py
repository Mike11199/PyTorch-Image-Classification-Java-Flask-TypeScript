"""Run one assistant request and return its final browser reply.

api/routes.py calls run_assistant with validated text and viewer settings. The
service reserves the single assistant request slot, creates the initial graph
state, and invokes the workflow built by agent/graph.py.

When the workflow finishes, its result contains browser edits or clarification
text. The route formats that result as JSON. The request slot is released even
when inference or validation fails, so a later request can still run.
"""

import threading
from time import perf_counter

from langchain_core.runnables import RunnableConfig

from .agent.graph import WORKFLOW_RECURSION_LIMIT, build_workflow
from .agent.state import AssistantState
from .telemetry import log_event
from .model.timing import measure_inference
from .types import AssistantResult
from .viewer.state import ViewerContext, ViewerRequest

workflow = build_workflow()
_request_slot = threading.BoundedSemaphore(1)


class AssistantBusyError(TimeoutError):
    """Another assistant request already owns the single request slot."""


def run_assistant(request: ViewerRequest, request_id: str) -> AssistantResult:
    """Run the agent once; fail promptly when busy and release the slot on any error."""
    started = perf_counter()
    context = ViewerContext.from_request(request)
    log_event('request_started', request_id, page=context.page,
              message=context.message[:200], available_class_count=len(context.available_classes))
    if not _request_slot.acquire(blocking=False):
        raise AssistantBusyError('The assistant is busy. Please try again shortly.')
    try:
        state: AssistantState = {'context': context, 'request_id': request_id}
        config: RunnableConfig = {'recursion_limit': WORKFLOW_RECURSION_LIMIT}
        with measure_inference() as timing:
            completed = workflow.invoke(state, config)
        result: AssistantResult = completed['result']
        result['timing'] = {
            'inference_ms': round(timing.milliseconds),
            'total_ms': round((perf_counter() - started) * 1000),
        }
        return result
    finally:
        _request_slot.release()
