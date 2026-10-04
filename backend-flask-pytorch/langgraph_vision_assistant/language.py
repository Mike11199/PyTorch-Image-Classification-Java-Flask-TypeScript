"""Recognize the small set of explicit phrases that must survive Qwen exactly."""

import re

NAMED_COLORS = {
    'red': '#ff0000', 'orange': '#ff8800', 'yellow': '#ffff00',
    'green': '#00ff00', 'blue': '#0000ff', 'purple': '#5b146e',
    'gray': '#444444', 'grey': '#444444', 'white': '#ffffff',
    'black': '#000000',
}

CLASS_ALIASES = {
    'bike': 'bicycle',
    'bikes': 'bicycle',
    'people': 'person',
}


def class_clauses(message, classes):
    """Yield each detected class and the words following its mention."""
    message_lower = message.lower()
    mentions = []
    for category in classes:
        pattern = rf'\b{re.escape(category.lower())}(?:s)?\b'
        mentions.extend((match.start(), match.end(), category)
                        for match in re.finditer(pattern, message_lower))
    available = set(classes)
    for alias, category in CLASS_ALIASES.items():
        if category in available:
            mentions.extend((match.start(), match.end(), category)
                            for match in re.finditer(rf'\b{alias}\b', message_lower))
    mentions.sort()
    for index, (_, end, category) in enumerate(mentions):
        next_start = mentions[index + 1][0] if index + 1 < len(mentions) else len(message)
        yield category, message[end:next_start].lower()


def _named_color(token):
    """Resolve an exact color or one with a single accidentally repeated letter."""
    if token in NAMED_COLORS:
        return NAMED_COLORS[token]
    for index in range(1, len(token)):
        if token[index] == token[index - 1]:
            repaired = token[:index] + token[index + 1:]
            if repaired in NAMED_COLORS:
                return NAMED_COLORS[repaired]
    return None


def color_mentions(message):
    """Yield color values in their textual order."""
    for match in re.finditer(r'#[0-9a-f]{6}\b|\b[a-z]+\b', message.lower()):
        token = match.group()
        color = token if token.startswith('#') else _named_color(token)
        if color:
            yield color


def requested_colors(message):
    """Return every named or hexadecimal color explicitly present in the request."""
    return set(color_mentions(message))


def explicit_filter_classes(message, classes):
    """Return classes from an explicit "only show" filter clause."""
    match = re.search(
        r'\b(?:only\s+show|show\s+only|only)\b(?P<body>.*?)(?='
        r'\b(?:and|then)\s+(?:make|color|paint|set|hide|show|count|find|jump|highlight)\b'
        r'|[.;]|$)',
        message.lower(),
    )
    if not match:
        return []
    found = [category for category, _ in class_clauses(match.group('body'), classes)]
    return list(dict.fromkeys(found))


def is_filter_only_request(message, classes):
    """Return whether an explicit class filter contains no second instruction."""
    remainder = re.sub(r'^\s*(?:only\s+show|show\s+only|only)\s+', '',
                       message.lower(), count=1)
    for category in classes:
        remainder = re.sub(rf'\b{re.escape(category.lower())}(?:s)?\b', '', remainder)
    available = set(classes)
    for alias, category in CLASS_ALIASES.items():
        if category in available:
            remainder = re.sub(rf'\b{alias}\b', '', remainder)
    remainder = re.sub(
        r'\b(?:please|the|detected|detection|detections|object|objects|'
        r'class|classes|category|categories|and|or)\b|[^a-z0-9]+',
        '', remainder,
    )
    return not remainder


def clause_target(clause, page):
    """Map explicit box and mask words to a color-action target."""
    boxes = bool(re.search(r'\bbox(?:es)?\b', clause))
    masks = bool(re.search(r'\bmasks?\b', clause))
    if boxes and masks:
        return 'both'
    if masks:
        return 'masks'
    if boxes or page == 'boxes':
        return 'boxes'
    return 'both'


def requests_layer_visibility(message):
    """Return whether the user explicitly asked to show or hide a whole layer."""
    layer = r'(?:box(?:es)?|masks?)'
    command = r'(?:show|hide|keep|enable|disable)'
    state = r'(?:on|off|only|visible|hidden)'
    message = message.lower()
    return bool(
        re.search(rf'\b{command}\b[^.]*\b{layer}\b', message)
        or re.search(rf'\b{layer}\b[^.]*\b{state}\b', message)
    )


def requests_full_mask_opacity(message):
    """Return whether the request explicitly asks for fully opaque masks."""
    message = message.lower()
    return bool(
        re.search(r'\bmasks?\b[^.]*\b(?:full|100\s*%)\b[^.]*\bopacity\b', message)
        or re.search(r'\b(?:full|100\s*%)\b[^.]*\b(?:mask\s+)?opacity\b', message)
    )
