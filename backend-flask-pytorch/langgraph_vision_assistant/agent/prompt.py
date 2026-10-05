"""Build the conversation sent to Qwen at the start of a request.

initial_messages supplies instructions, example tool conversations, current
viewer settings, and the user's request. The examples demonstrate arguments;
they are never executed and do not supply the current viewer's object names.

agent/turn.py uses these messages for the first call. Later calls reuse the
conversation with tool results and correction feedback. Tool argument schemas
come from tools/registry.py and are supplied separately by model/client.py.
"""

import json

from langchain_core.messages import AnyMessage, HumanMessage, SystemMessage

from .examples import example_messages

from ..types import ViewerContext

SYSTEM_PROMPT = '''You edit an object-detection viewer by calling tools.
Make only the requested changes. Use exact detected class names from the context.
Handle every requested object; requests joined by "and" can require multiple tool calls.
Resolve class plurals. Copy each requested color word exactly, even if misspelled;
the color tool resolves names and typos. For custom shades, supply a hex color.
Coloring defaults to all layers and does not change visibility or opacity.
Boxes include text labels. Boxes, masks, and labels are layers, not object classes.
"Show all" uses restore_all_visibility. "Show all categories" only clears the class filter.
Use tools for counts and playback; the browser performs these operations.
Ask briefly if the request is unclear. Retry all requested edits after a tool error.
The sample conversations demonstrate tool usage. Use the current viewer context
for the actual request, not the sample objects.
'''



def initial_messages(context: ViewerContext) -> list[AnyMessage]:
    """Keep the user's request separate from instructions and the viewer snapshot."""
    snapshot = {key: context[key] for key in ('page', 'availableClasses', 'view')}
    return [
        SystemMessage(SYSTEM_PROMPT),
        *example_messages(),
        SystemMessage('Current viewer context: ' + json.dumps(snapshot) +
                      '\nOnly act on the next user request. Keep each object paired with its own color word; '
                      'copy misspelled color words rather than guessing or swapping them.'),
        HumanMessage(context['message']),
    ]
