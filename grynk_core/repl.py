"""Grynk interactive REPL."""

import sys
from .interpreter import Interpreter, run_source
from .lexer import tokenize
from .parser import parse
from .types import grynk_str
from .errors import GrynkError, grynk_exit_error

try:
    from colorama import Fore, Style, init as _cinit
    _cinit(autoreset=True)
    _CYAN  = Fore.CYAN + Style.BRIGHT
    _GREEN = Fore.GREEN
    _GRAY  = Fore.WHITE
    _RESET = Style.RESET_ALL
except ImportError:
    _CYAN = _GREEN = _GRAY = _RESET = ''

BANNER = f"""
{_CYAN}╔══════════════════════════════════╗
║   ██████╗ ██████╗ ██╗   ██╗███╗  ║
║  ██╔════╝ ██╔══██╗╚██╗ ██╔╝████╗ ║
║  ██║  ███╗██████╔╝ ╚████╔╝ ██╔██╗║
║  ██║   ██║██╔══██╗  ╚██╔╝  ██║╚██║
║  ╚██████╔╝██║  ██║   ██║   ██║ ╚█║
║   ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚║
╚══════════════════════════════════╝{_RESET}
  {_GREEN}Grynk v1.0.0  — Powerful. Fast. Alive.{_RESET}
  Type {_CYAN}exit{_RESET} or press Ctrl+C to quit.
"""


def run_repl():
    print(BANNER)
    interp = Interpreter()
    buf = []
    depth = 0

    while True:
        try:
            prompt = f'{_CYAN}grynk>{_RESET} ' if depth == 0 else f'{_CYAN}  ...>{_RESET} '
            try:
                line = input(prompt)
            except EOFError:
                print()
                break

            if line.strip() in ('exit', 'quit', ':q'):
                print(f'{_GREEN}Goodbye! 👋{_RESET}')
                break

            buf.append(line)
            depth += line.count('{') - line.count('}')

            if depth > 0:
                continue

            source = '\n'.join(buf)
            buf = []
            depth = 0

            if not source.strip():
                continue

            try:
                tokens = tokenize(source)
                ast = parse(tokens)
                # Execute each statement and print non-None results
                from .interpreter import Interpreter as _I, ReturnSignal
                for stmt in ast.body:
                    result = interp.exec(stmt, interp.globals)
                    if result is not None:
                        print(f'{_GRAY}{grynk_str(result)}{_RESET}')
            except GrynkError as e:
                print(e.display(), file=sys.stderr)
            except Exception as e:
                print(f'{_CYAN}✖ Internal:{_RESET} {e}', file=sys.stderr)

        except KeyboardInterrupt:
            print()
            if buf:
                buf = []
                depth = 0
                print('(input cleared)')
            else:
                print(f'{_GREEN}Goodbye! 👋{_RESET}')
                break
