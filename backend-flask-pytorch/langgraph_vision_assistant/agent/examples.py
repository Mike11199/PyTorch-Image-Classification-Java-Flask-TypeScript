"""Show Qwen complete examples of requests, tool calls, and tool feedback.

These sample conversations teach argument usage. They are never executed and
do not replace the user's request or the current viewer's detected classes.
"""

from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, ToolCall, ToolMessage
from pydantic import JsonValue


EXAMPLES: list[tuple[str, list[tuple[str, dict[str, JsonValue]]]]] = [
    ('Make dog teal and cat gold', [('set_class_colors', {'colors': [
        {'className': 'dog', 'color': 'teal', 'layers': ['boxes', 'masks']},
        {'className': 'cat', 'color': 'gold', 'layers': ['boxes', 'masks']},
    ]})]),
    ('Make bicycle masks orange and truck boxes pink', [('set_class_colors', {'colors': [
        {'className': 'bicycle', 'color': 'orange', 'layers': ['masks']},
        {'className': 'truck', 'color': 'pink', 'layers': ['boxes']},
    ]})]),
    ('Only show trucks', [('set_visible_classes', {'classes': ['truck']})]),
    ('Hide bicycles', [('hide', {'targets': ['bicycle']})]),
    ('Show labels only', [('set_layers', {'layers': ['labels']})]),
    ('Hide labels', [('hide', {'targets': ['labels']})]),
    ('Show boxes and labels at half opacity', [('set_layers', {'layers': ['boxes', 'labels'], 'opacity': 0.5})]),
    ('Make dog boxes only cyan', [('set_class_colors', {'colors': [
        {'className': 'dog', 'color': 'cyan', 'layers': ['boxes']},
    ]})]),
    ('Jump to the frame with the most bicycles', [('seek_detection', {'className': 'bicycle', 'mode': 'peak'})]),
    ('Make dog boxes and masks green', [('set_class_colors', {'colors': [
        {'className': 'dog', 'color': 'green', 'layers': ['boxes', 'masks']},
    ]})]),
    ('Show masks and labels only', [('set_layers', {'layers': ['masks', 'labels']})]),
    ('Make truck gren and bicycle ornage', [('set_class_colors', {'colors': [
        {'className': 'truck', 'color': 'gren'},
        {'className': 'bicycle', 'color': 'ornage'},
    ]})]),
    ('Show every category', [('set_visible_classes', {'classes': []})]),
    ('Show everything', [('restore_all_visibility', {})]),
]


def example_messages() -> list[AnyMessage]:
    """Format examples as native tool conversations, with matching result IDs."""
    messages: list[AnyMessage] = []
    for index, (request, calls) in enumerate(EXAMPLES):
        tool_calls: list[ToolCall] = [
            {'name': name, 'args': arguments, 'id': f'example_{index}_{number}', 'type': 'tool_call'}
            for number, (name, arguments) in enumerate(calls)
        ]
        messages.extend([HumanMessage(request), AIMessage(content='', tool_calls=tool_calls)])
        messages.extend(ToolMessage('Commands prepared.', tool_call_id=str(call['id'])) for call in tool_calls)
    return messages
