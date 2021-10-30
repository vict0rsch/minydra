from os.path import expandvars
from pathlib import Path


def split_line(line, length):
    items = [
        line[length * i : length * (i + 1)] for i in range(len(line) // length + 1)
    ]
    return [i for i in items if i.lstrip()]


def resolve_path(path):
    """
    fully resolve a path:
    resolve env vars ($HOME etc.) -> expand user (~) -> make absolute

    Returns:
        pathlib.Path: resolved absolute path
    """
    return Path(expandvars(str(path))).expanduser().resolve()
