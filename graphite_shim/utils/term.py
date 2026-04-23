from __future__ import annotations

import contextlib
import enum
import functools
import io
import os
import re
import sys
import termios
import tty
from collections.abc import Callable, Generator, Sequence
from typing import Any

FORCE_COLOR = "--color" in sys.argv


def _print(msg: str, *, end: str = "\n", get_file: Callable[[], io.StringIO | Any]) -> None:
    """Convenience function for printing colored output."""
    file = get_file()

    # strip escape codes if not a TTY
    msg = colorify(msg) if FORCE_COLOR or file.isatty() else re.sub(r"@\(\w+\)", "", msg)

    file.write(msg)
    file.write(end)


print = functools.partial(_print, get_file=lambda: sys.stdout)
printerr = functools.partial(_print, get_file=lambda: sys.stderr)


@contextlib.contextmanager
def suppress_output() -> Generator[None]:
    with (
        open(os.devnull, "w") as devnull,
        contextlib.redirect_stdout(devnull),
        contextlib.redirect_stderr(devnull),
    ):
        yield


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

    def ask_oneof[T](
        self,
        prompt: str,
        options: Sequence[T],
        *,
        render: Callable[[T], str] = str,
        start_index: int = 0,
    ) -> T:
        num_options = len(options)
        with hidden_cursor():
            curr_index = start_index
            search: str | None = None
            while True:
                opts_to_show = [
                    (i, opt)
                    for i, option in enumerate(options)
                    for opt in [render(option)]
                    if search is None or search in opt
                ]
                if len(opts_to_show) > 0 and not any(i == curr_index for i, _ in opts_to_show):
                    curr_index = opts_to_show[0][0]
                    continue

                num_lines = 1
                print(f"@(yellow){prompt}:")
                for i, opt in opts_to_show:
                    cursor = "@(bg-gray)>" if i == curr_index else " "
                    print(f"@(cyan){cursor} @(yellow){opt}")
                    num_lines += 1
                if search is not None:
                    num_lines += 1
                    print(f"@(gray)Filter: {search}▎")

                c = self.get_raw()

                # Move cursor back to start
                print("\033[F\033[K" * num_lines, end="")

                match c:
                    case RawKey.ENTER:
                        return options[curr_index]
                    case RawKey.UP:
                        curr_index = (curr_index - 1) % num_options
                    case RawKey.DOWN:
                        curr_index = (curr_index + 1) % num_options
                    case RawKey.CTRL_C:
                        raise KeyboardInterrupt
                    case RawKey.CTRL_W:
                        search = None
                    case RawKey.BACKSPACE:
                        search = None if search is None or len(search) == 1 else search[:-1]
                    case RawKey.OTHER:
                        pass
                    case _:
                        search = (search or "") + c

    def get_raw(self) -> RawKey | str:
        with raw_tty():
            key = sys.stdin.read(1)
            if key == "\x1b":
                key += sys.stdin.read(2)
        match key:
            case "\x1b[A":
                return RawKey.UP
            case "\x1b[B":
                return RawKey.DOWN
            case "\r" | "\n":
                return RawKey.ENTER
            case "\x03":
                return RawKey.CTRL_C
            case "\x17":
                return RawKey.CTRL_W
            case "\x7f":
                return RawKey.BACKSPACE
            case c:
                return c if "\x21" <= c <= "\x7e" else RawKey.OTHER


def colorify(msg: str, *, reset: bool = True) -> str:
    """
    Make a message colorful.

    The message may have color codes like: "This is @(red)RED@(reset)".
    """
    if reset:
        msg += "@(reset)"

    def replace(match: re.Match[str]) -> str:
        return to_escape_code(CODES[match.group(1)])

    return re.sub(r"@\(([\w-]+)\)", replace, msg)


# ----- Low level API ----- #

CODES = {
    "reset": 0,
    "fg-reset": 39,
    "bold": 1,
    # foreground colors
    "red": 31,
    "green": 32,
    "yellow": 33,
    "blue": 34,
    "magenta": 35,
    "cyan": 36,
    "gray": 90,
    # background colors
    "bg-gray": 100,
}


def to_escape_code(*codes: int) -> str:
    # https://stackoverflow.com/a/33206814/4966649
    return f"\033[{';'.join(str(x) for x in codes)}m"


class RawKey(enum.StrEnum):
    UP = enum.auto()
    DOWN = enum.auto()
    ENTER = enum.auto()
    CTRL_C = enum.auto()
    CTRL_W = enum.auto()
    BACKSPACE = enum.auto()
    OTHER = enum.auto()


@contextlib.contextmanager
def raw_tty() -> Generator[None]:
    fd = sys.stdin.fileno()
    old_settings = tty.setraw(fd)
    try:
        yield
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


@contextlib.contextmanager
def hidden_cursor() -> Generator[None]:
    sys.stdout.write("\033[?25l")
    sys.stdout.flush()
    try:
        yield
    finally:
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()
