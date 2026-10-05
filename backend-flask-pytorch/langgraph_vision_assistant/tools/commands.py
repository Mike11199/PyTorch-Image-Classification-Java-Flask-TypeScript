"""Package a browser edit in the form LangGraph expects from a tool.

A tool in viewer.py calls prepared with one or more edit dictionaries. For
example, showing masks at full opacity prepares visibility and opacity edits.
ToolNode stores feedback in ToolMessage.content and the list of edits in artifact.

That split lets Qwen read tool feedback while tools/results.py collects the
structured edits for the browser. Preparing an edit does not apply it; all tools
in the attempt must succeed before their edits can be returned.
"""

from ..commands import ViewerCommand
from ..types import PreparedCommand


def prepared(*commands: ViewerCommand) -> PreparedCommand:
    """Pair feedback with the browser edits produced by one tool call."""
    return 'Commands prepared; the browser has not applied them yet.', list(commands)
