"""Send a conversation and tool definitions to the local Qwen model.

ask_qwen in agent/nodes.py calls call_model. It acquires the shared model session,
converts LangChain messages and tool definitions to the local chat API format,
and converts the server's reply back into an AIMessage containing text or calls.

llama.cpp parses Qwen's native tool-call syntax. model/validation.py then checks
the reply before the graph executes any calls. Local process ownership lives
in runtime.py; this module handles the conversation crossing that boundary.
"""

from time import perf_counter
from typing import Any
from collections.abc import Sequence

from langchain_core.messages import AIMessage, AnyMessage, convert_to_messages, convert_to_openai_messages
from langchain_core.tools import BaseTool
from langchain_core.utils.function_calling import convert_to_openai_tool

from ..telemetry import log_event
from .timing import record_inference


def call_model(messages: list[AnyMessage], tools: Sequence[BaseTool], request_id: str) -> AIMessage:
    """Run local inference under the shared model lock and return parsed tool calls.

    llama.cpp handles Qwen's chat template and tool syntax; this module only
    converts standard API messages. Viewer settings are already in the messages.
    """
    from runtime.model_runtime import model_session

    started = perf_counter()
    with model_session('llm', request_id=request_id) as model:
        inference_started = perf_counter()
        try:
            response = model.create_chat_completion(**completion_payload(messages, tools))
        finally:
            inference_ms = (perf_counter() - inference_started) * 1000
            record_inference(inference_ms)
    message = assistant_message(response)
    log_event('model_completed', request_id, model=model.name,
              duration_ms=round((perf_counter() - started) * 1000),
              setup_ms=round((inference_started - started) * 1000),
              inference_ms=round(inference_ms), timings=response.get('timings'),
              usage=response.get('usage'),
              tool_count=len(message.tool_calls))
    return message


def completion_payload(messages: list[AnyMessage], tools: Sequence[BaseTool]) -> dict[str, object]:
    """Convert chat history and tool definitions to llama.cpp's API format."""
    return {
        'messages': convert_to_openai_messages(messages),
        'tools': [convert_to_openai_tool(tool) for tool in tools],
        'tool_choice': 'auto', 'parallel_tool_calls': True,
        'temperature': 0, 'top_p': 0.8, 'top_k': 20, 'min_p': 0,
        'max_tokens': 768,
        'chat_template_kwargs': {'enable_thinking': False},
    }


def assistant_message(response: dict[str, Any]) -> AIMessage:
    """Decode the server response and reject truncated or non-assistant output."""
    choice = response['choices'][0]
    if choice['finish_reason'] == 'length':
        raise ValueError('The tool response exceeded its token limit.')
    message = convert_to_messages([choice['message']])[0]
    if not isinstance(message, AIMessage):
        raise ValueError('Expected an assistant response from the model.')
    return message
