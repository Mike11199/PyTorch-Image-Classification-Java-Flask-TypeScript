"""Build the conversation sent to Qwen at the start of a request.

initial_messages combines our instructions and the current viewer settings in
a SystemMessage, then adds the user's text as a separate HumanMessage. The
instructions explain how to choose colors, preserve settings, and handle errors.

agent/turn.py uses these messages for the first call. Later calls reuse the
conversation with tool results and correction feedback. Tool argument schemas
come from tools/registry.py and are supplied separately by model/client.py.
"""

import json

from langchain_core.messages import AnyMessage, HumanMessage, SystemMessage

from ..types import ViewerContext

SYSTEM_PROMPT = '''You control an object-detection viewer using tools.
Use the detected class names exactly; resolve plurals and familiar aliases to them.
Interpret obvious typos, including color names. Convert any requested color/shade
into a six-digit hex code. Preserve literal hex codes exactly and keep every color
paired with its requested class. Handle ALL requested changes in one tool batch.
For example, "cats red and dogs puple" means cat=#ff0000 and dog=#800080.
Teal is #008080; dark blue is #00008b. Other colors are allowed: choose their hex codes.
Only change what the user asks. A color change must not change visibility or opacity.
Omit color target unless the user explicitly names a layer. The tool supplies
the correct page default. Preserve unrelated layer settings.
Use selectedClasses for words like "those". Read viewer context when needed.
Tools prepare browser commands; they do not execute them or compute counts here.
Never invent counts or claim commands were applied. For unsupported/ambiguous
requests, give a brief explanation or question (at most 240 characters).
After a tool error, resend the entire corrected batch; nothing was applied.
'''


def initial_messages(context: ViewerContext) -> list[AnyMessage]:
    """Keep the user's request separate from instructions and the viewer snapshot."""
    snapshot = {key: context[key] for key in ('page', 'availableClasses', 'view')}
    return [
        SystemMessage(SYSTEM_PROMPT + '\nViewer context: ' + json.dumps(snapshot)),
        HumanMessage(context['message']),
    ]
