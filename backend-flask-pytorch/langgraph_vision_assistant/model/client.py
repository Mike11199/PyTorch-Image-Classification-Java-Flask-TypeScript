"""Inference adapter between the graph and the local Qwen runtime.

call_model receives chat history and tool definitions, takes the shared inference
lock, and returns an AIMessage. llama.cpp handles the model's native tool syntax;
there is no text parser here. Process startup and shutdown live in runtime.py.
"""

from time import perf_counter
from typing import Any
from collections.abc import Sequence

from langchain_core.messages import AIMessage, AnyMessage, convert_to_messages, convert_to_openai_messages
from langchain_core.tools import BaseTool
from langchain_core.utils.function_calling import convert_to_openai_tool

from ..telemetry import log_event


def call_model(messages: list[AnyMessage], tools: Sequence[BaseTool], request_id: str) -> AIMessage:
    """Run local inference under the shared model lock and return parsed tool calls.

    llama.cpp handles Qwen's chat template and tool syntax; this module only
    converts standard API messages. Viewer settings are already in the messages.
    """
    from model_runtime import model_session

    started = perf_counter()
    with model_session('llm', request_id=request_id) as model:
        response = model.create_chat_completion(**completion_payload(messages, tools))
    message = assistant_message(response)
    log_event('model_completed', request_id, model='qwen3-0.6b',
              duration_ms=round((perf_counter() - started) * 1000),
              tool_count=len(message.tool_calls))
    return message


def completion_payload(messages: list[AnyMessage], tools: Sequence[BaseTool]) -> dict[str, object]:
    """Convert chat history and tool definitions to llama.cpp's API format."""
    return {
        'messages': convert_to_openai_messages(messages),
        'tools': [convert_to_openai_tool(tool) for tool in tools],
        'tool_choice': 'auto', 'parallel_tool_calls': True,
        'temperature': 0, 'max_tokens': 768,
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
