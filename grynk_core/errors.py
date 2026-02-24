"""Grynk error handling — friendly, colored, with line numbers and did-you-mean."""

import difflib
import sys

try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
    _HAS_COLOR = True
except ImportError:
    _HAS_COLOR = False


def _red(s):
    return (Fore.RED + s + Style.RESET_ALL) if _HAS_COLOR else s

def _yellow(s):
    return (Fore.YELLOW + s + Style.RESET_ALL) if _HAS_COLOR else s

def _cyan(s):
    return (Fore.CYAN + s + Style.RESET_ALL) if _HAS_COLOR else s

def _bold(s):
    return (Style.BRIGHT + s + Style.RESET_ALL) if _HAS_COLOR else s


class GrynkError(Exception):
    """Base Grynk runtime / parse error with pretty display."""
    def __init__(self, message, line=None, kind="Runtime Error", suggestions=None):
        self.message = message
        self.line = line
        self.kind = kind
        self.suggestions = suggestions or []
        super().__init__(message)

    def display(self):
        loc = f" (line {self.line})" if self.line is not None else ""
        header = _red(f"✖ Grynk {self.kind}{loc}:") + " " + _bold(self.message)
        lines = [header]
        if self.suggestions:
            best = self.suggestions[0]
            lines.append(_yellow(f"  → did you mean '{best}'?"))
        return "\n".join(lines)

    def __str__(self):
        return self.display()


class GrynkParseError(GrynkError):
    def __init__(self, message, line=None, suggestions=None):
        super().__init__(message, line=line, kind="Parse Error", suggestions=suggestions)


class GrynkRuntimeError(GrynkError):
    def __init__(self, message, line=None, suggestions=None):
        super().__init__(message, line=line, kind="Runtime Error", suggestions=suggestions)


class GrynkTypeError(GrynkError):
    def __init__(self, message, line=None):
        super().__init__(message, line=line, kind="Type Error")


class GrynkNameError(GrynkError):
    def __init__(self, name, line=None, known_names=None):
        suggestions = []
        if known_names:
            close = difflib.get_close_matches(name, known_names, n=3, cutoff=0.6)
            suggestions = close
        super().__init__(
            f"Undefined variable '{name}'",
            line=line,
            kind="Runtime Error",
            suggestions=suggestions,
        )


def grynk_exit_error(err):
    """Print a GrynkError and exit with code 1."""
    if isinstance(err, GrynkError):
        print(err.display(), file=sys.stderr)
    else:
        print(_red(f"✖ Grynk Internal Error: {err}"), file=sys.stderr)
    sys.exit(1)
