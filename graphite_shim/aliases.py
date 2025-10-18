from collections.abc import Mapping, Sequence
from pathlib import Path

ALIASES_FILE = Path.home() / ".config/graphite/aliases"
DEFAULT_ALIASES_CONTENT = """
ls log short
ll log long
ss submit --stack
"""

def load_aliases() -> Mapping[str, Sequence[str]]:
    try:
        aliases_content = ALIASES_FILE.read_text()
    except FileNotFoundError:
        aliases_content = DEFAULT_ALIASES_CONTENT

    return {
        alias: args
        for line in aliases_content.splitlines()
        if not line.startswith("#") and line.strip() != ""
        for alias, *args in [line.split()]
    }
