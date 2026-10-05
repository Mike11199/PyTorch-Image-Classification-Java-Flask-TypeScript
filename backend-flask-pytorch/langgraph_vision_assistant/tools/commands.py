"""Give a tool's output two parts: feedback for Qwen and an edit for the browser.

viewer.py calls prepared with an edit dictionary, such as a set_class_color
command. It returns (feedback text, edit dictionary). LangGraph's ToolNode puts
those into ToolMessage.content and ToolMessage.artifact respectively.
tools/results.py later collects the artifact dictionaries for the HTTP reply.
The browser applies them only after every tool in the attempt succeeds.
"""

from ..commands import ViewerCommand
from ..types import PreparedCommand


def prepared(command: ViewerCommand) -> PreparedCommand:
    """Return model feedback and the command artifact expected by ToolNode."""
    return 'Command prepared; the browser has not applied it yet.', command
