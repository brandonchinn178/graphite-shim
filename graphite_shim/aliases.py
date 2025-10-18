from collections.abc import Mapping, Sequence
from pathlib import Path

ALIASES_FILE = Path.home() / ".config/graphite/aliases"
DEFAULT_ALIASES = {
    "ls": ["log", "short"],
    "ll": ["log", "long"],
    "ss": ["submit", "--stack"],
    # Technically, graphite automatically allows any prefix of a command,
    # but we'll just represent them as aliases
    "s": ["submit"],
}

def load_aliases() -> Mapping[str, Sequence[str]]:
    try:
        aliases_content = ALIASES_FILE.read_text()
    except FileNotFoundError:
        aliases_content = ""

    aliases = {
        alias: args
        for line in aliases_content.splitlines()
        if not line.startswith("#") and line.strip() != ""
        for alias, *args in [line.split()]
    }

    return {**DEFAULT_ALIASES, **aliases}
