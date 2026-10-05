"""Package a browser edit in the form LangGraph expects from a tool.

A tool in viewer.py calls prepared with an edit dictionary, such as a color
change. We pair it with feedback explaining that the edit has been prepared.
ToolNode stores the feedback in ToolMessage.content and the edit in artifact.

That split lets Qwen read tool feedback while tools/results.py collects the
structured edits for the browser. Preparing an edit does not apply it; all tools
in the attempt must succeed before their edits can be returned.
"""

from ..commands import ViewerCommand
from ..types import PreparedCommand


def prepared(command: ViewerCommand) -> PreparedCommand:
    """Return model feedback and the command artifact expected by ToolNode."""
    return 'Command prepared; the browser has not applied it yet.', command
