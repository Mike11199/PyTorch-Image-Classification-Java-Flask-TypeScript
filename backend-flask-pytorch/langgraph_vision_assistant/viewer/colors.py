"""Convert requested colors to the hex format used by the browser.

Qwen chooses the class and requested color. Pillow resolves standard CSS color
names, so the model does not have to calculate their RGB codes. Custom hex codes
are accepted too. Unsupported values become tool errors for Qwen to correct.
"""

from difflib import get_close_matches

from PIL import ImageColor


def color_name(value: str) -> str:
    """Correct an unambiguous near-match to a CSS name; leave hex codes alone."""
    name = value.strip().lower()
    if name.startswith('#') or name in ImageColor.colormap:
        return name
    matches = get_close_matches(name, ImageColor.colormap, n=2, cutoff=0.8)
    return matches[0] if len(matches) == 1 else name


def color_hex(color: str) -> str:
    """Return an opaque RGB color as lowercase #rrggbb."""
    try:
        rgb = ImageColor.getrgb(color_name(color))
    except ValueError as error:
        raise ValueError('Use a CSS color name or a six-digit hex color.') from error
    if len(rgb) != 3:
        raise ValueError('Use an opaque color; control transparency with opacity.')
    red, green, blue = rgb
    return f'#{red:02x}{green:02x}{blue:02x}'
