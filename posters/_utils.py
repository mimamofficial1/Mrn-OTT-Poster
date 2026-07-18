import re


def find_square_image(mapping):
    """Scan a dict of {key: url} (or list of such dicts) for any key whose
    name encodes a WxH pair where width == height (i.e. a 1:1 / square
    image variant). Works regardless of the exact naming convention used
    by the source API/platform.

    Returns the URL string if found, otherwise None. Never raises -
    callers can safely do `"square": find_square_image(some_dict)` and
    get null when no square art is available instead of an error.
    """
    if not mapping:
        return None

    items = []
    if isinstance(mapping, dict):
        items = mapping.items()
    elif isinstance(mapping, (list, tuple)):
        for entry in mapping:
            if isinstance(entry, dict):
                items = list(items) + list(entry.items())

    for key, value in items:
        if not value or not isinstance(key, str):
            continue
        m = re.search(r"(\d+)[x_](\d+)", key)
        if m and m.group(1) == m.group(2):
            return value if isinstance(value, str) else None

    return None
