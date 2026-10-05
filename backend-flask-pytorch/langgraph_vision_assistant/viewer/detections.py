"""Prepare counting, highlighting, and seeking commands for the browser.

Python checks class names and page capabilities. The browser owns the detector
results and playback, so it computes the actual count, selection, or seek time.
"""

from typing import Literal

from .checks import require_classes
from .commands import CountCommand, SelectCommand, SeekCommand
from .state import ViewerContext

Region = Literal['all', 'left', 'right']
Selection = Literal['leftmost', 'rightmost', 'largest', 'least_confident']
Seek = Literal['first', 'next', 'peak']


def count_detections(classes: list[str], region: Region, context: ViewerContext) -> CountCommand:
    """Ask the browser to count matching visible detections in a region."""
    require_classes(classes, context)
    return {'type': 'count_detections', 'classes': classes, 'region': region}


def select_detection(class_name: str, mode: Selection, context: ViewerContext) -> SelectCommand:
    """Ask the browser to select one detection by position, size, or confidence."""
    require_classes([class_name], context)
    return {'type': 'select_detection', 'className': class_name, 'mode': mode}


def seek_detection(class_name: str, mode: Seek, context: ViewerContext) -> SeekCommand:
    """Ask a video viewer to seek to a matching detection."""
    require_classes([class_name], context)
    if context.page != 'video':
        raise ValueError('Seeking is only available on the video page.')
    return {'type': 'seek_detection', 'className': class_name, 'mode': mode}
