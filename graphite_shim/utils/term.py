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


class Prompter:
    def input(self, prompt: str) -> str:
        return input(colorify(prompt))

    def ask(self, prompt: str, *, default: str = "") -> str:
        suffix = f" [{default}]" if default else ":"
        resp = self.input(f"@(yellow){prompt}{suffix} ").strip()
        return resp if resp else default

    def ask_yesno(self, prompt: str, *, default: bool) -> bool:
        default_disp = "Y/n" if default else "y/N"
        resp = self.ask(prompt, default=default_disp)
        if resp == default_disp:
            return default
        return resp.lower() in ("y", "yes")


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
