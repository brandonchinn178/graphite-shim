import functools
import io
import re
import sys
from collections.abc import Callable
from typing import Any


def _print(msg: str, *, end: str = "\n", get_file: Callable[[], io.StringIO | Any]) -> None:
    """Convenience function for printing colored output."""
    file = get_file()

    # strip escape codes if not a TTY
    msg = colorify(msg) if file.isatty() else re.sub(r"@\(\w+\)", "", msg)

    file.write(msg)
    file.write(end)


print = functools.partial(_print, get_file=lambda: sys.stdout)
printerr = functools.partial(_print, get_file=lambda: sys.stderr)

builtin_input = input


def input(msg: str) -> str:
    """Convenience function for asking user input with color."""
    return builtin_input(colorify(msg))


def colorify(msg: str, *, reset: bool = True) -> str:
    """
    Make a message colorful.

    The message may have color codes like: "This is @(red)RED@(reset)".
    """
    if reset:
        msg += "@(reset)"

    def replace(match: re.Match[str]) -> str:
        return to_escape_code(CODES[match.group(1)])

    return re.sub(r"@\((\w+)\)", replace, msg)


# ----- Low level API ----- #

CODES = {
    "reset": 0,
    "bold": 1,
    # foreground colors
    "red": 31,
    "green": 32,
    "yellow": 33,
    "blue": 34,
    "magenta": 35,
    "cyan": 36,
}


def to_escape_code(*codes: int) -> str:
    # https://stackoverflow.com/a/33206814/4966649
    return f"\033[{';'.join(str(x) for x in codes)}m"
