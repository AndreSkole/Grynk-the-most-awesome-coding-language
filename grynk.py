"""
Grynk CLI entry point.

Usage:
  grynk run file.grk
  grynk file.grk
  grynk repl
  grynk new <name>
  grynk help
  grynk version
"""

import sys
import os

# Force UTF-8 on Windows (use reconfigure to not break colorama)
if sys.platform == 'win32':
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

__version__ = "1.0.0"

try:
    from colorama import Fore, Style, init as _cinit
    _cinit(autoreset=True)
    _CYAN   = Fore.CYAN + Style.BRIGHT
    _GREEN  = Fore.GREEN + Style.BRIGHT
    _YELLOW = Fore.YELLOW
    _RED    = Fore.RED + Style.BRIGHT
    _RESET  = Style.RESET_ALL
    _BOLD   = Style.BRIGHT
except ImportError:
    _CYAN = _GREEN = _YELLOW = _RED = _RESET = _BOLD = ''


HELP_TEXT = f"""
{_CYAN}╔══════════════════════════════════════════════════╗
║           GRYNK  — Powerful. Fast. Alive.        ║
╚══════════════════════════════════════════════════╝{_RESET}

{_BOLD}USAGE{_RESET}
  grynk run <file.grk>     Run a .grk source file
  grynk <file.grk>         Same — direct execution
  grynk repl               Start the interactive shell
  grynk new <name>         Scaffold a new project file
  grynk help               Show this help reference
  grynk version            Show version info

{_BOLD}SYNTAX OVERVIEW{_RESET}
  {_CYAN}Variables:{_RESET}        let x = 10 | mut counter = 0
  {_CYAN}Functions:{_RESET}        fn greet(name) {{ say "Hi {{name}}!" }}
  {_CYAN}Print:{_RESET}            say "Hello, {{name}}"
  {_CYAN}Input:{_RESET}            let name = ask("Your name? ")
  {_CYAN}Loops:{_RESET}            loop 5 times {{ ... }} | for x in list {{ }}
  {_CYAN}Conditions:{_RESET}       if x > 0 {{ }} elif x == 0 {{ }} else {{ }}
  {_CYAN}Match:{_RESET}            match val {{ case 1 {{ }} case _ {{ }} }}
  {_CYAN}Try/Catch:{_RESET}        try {{ }} catch(e) {{ }}
  {_CYAN}Pipe:{_RESET}             [1,2,3] |> gx.sort() |> gx.unique()
  {_CYAN}Power:{_RESET}            2 ** 10
  {_CYAN}Interpolation:{_RESET}    "Hello {{name}}, score: {{score * 2}}"
  {_CYAN}Comments:{_RESET}         # this is a comment

{_BOLD}BUILT-IN gx OBJECT (zero imports){_RESET}
  {_YELLOW}Web:{_RESET}    gx.get(url)  gx.post(url, body)  gx.scrape(url, tag)
  {_YELLOW}AI:{_RESET}     gx.ai(prompt)  gx.ai_sentiment(t)  gx.ai_summarize(t,n)
  {_YELLOW}Crypto:{_RESET} gx.hash(s)  gx.sha256(s)  gx.b64encode(s)  gx.uuid()
  {_YELLOW}Time:{_RESET}   gx.now()  gx.sleep(ms)  gx.bench(fn, runs)
  {_YELLOW}Files:{_RESET}  gx.read(p)  gx.write(p,s)  gx.read_json(p)
  {_YELLOW}Math:{_RESET}   gx.sqrt()  gx.avg(list)  gx.clamp(v,lo,hi)  gx.pi()
  {_YELLOW}Data:{_RESET}   gx.range(a,b)  gx.sort(l)  gx.unique(l)  gx.chunk(l,n)
  {_YELLOW}OS:{_RESET}     gx.env(k)  gx.run(cmd)  gx.cwd()  gx.platform()
  {_YELLOW}Output:{_RESET} gx.banner(t)  gx.table(d)  gx.color(c,t)  gx.log(m)
  {_YELLOW}Rand:{_RESET}   gx.rand()  gx.randint(a,b)  gx.uuid()  gx.token(n)

{_BOLD}TYPE METHODS{_RESET}
  {_GREEN}String:{_RESET}  .upper() .lower() .trim() .split(sep) .replace(a,b) .len()
  {_GREEN}List:{_RESET}    .push(v) .map(fn) .filter(fn) .sort() .sum() .join(sep)
  {_GREEN}Dict:{_RESET}    .keys() .values() .get(k) .set(k,v) .has(k) .merge(d)
  {_GREEN}Number:{_RESET}  .abs() .floor() .ceil() .round(d) .pow(n) .sqrt()
"""

NEW_TEMPLATE = '''\
# {name}.grk — Created with Grynk v1.0.0
# Powerful. Fast. Alive.

gx.banner("{name}", "cyan")

let author = ask("Your name? ")
say "Welcome, {{author}}! Let\\'s build something great."

fn greet(who, times = 1) {{
    loop times times {{
        say "Hello, {{who}}!"
    }}
}}

greet(author, 3)

let nums = gx.range(1, 11)
fn is_even(n) {{ return n % 2 == 0 }}
say "Sum of evens 1–10: {{nums.filter(is_even).sum()}}"

let resp = gx.get("https://httpbin.org/get")
say "Status: {{resp.status}}"
'''


def main():
    args = sys.argv[1:]

    if not args:
        print(f'{_CYAN}Grynk v{__version__} — Powerful. Fast. Alive.{_RESET}')
        print(f'Run {_BOLD}grynk help{_RESET} for usage.')
        sys.exit(0)

    cmd = args[0]

    # grynk version
    if cmd == 'version':
        print(f'{_CYAN}Grynk{_RESET} v{_BOLD}{__version__}{_RESET}  — Powerful. Fast. Alive.')
        sys.exit(0)

    # grynk help
    if cmd == 'help':
        print(HELP_TEXT)
        sys.exit(0)

    # grynk repl
    if cmd == 'repl':
        from grynk_core.repl import run_repl
        run_repl()
        sys.exit(0)

    # grynk new <name>
    if cmd == 'new':
        if len(args) < 2:
            print(f'{_RED}✖ Usage: grynk new <project-name>{_RESET}')
            sys.exit(1)
        name = args[1].replace(' ', '_')
        filename = f'{name}.grk'
        if os.path.exists(filename):
            print(f'{_YELLOW}⚠ File already exists: {filename}{_RESET}')
            sys.exit(1)
        content = NEW_TEMPLATE.replace('{name}', name)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'{_GREEN}✔ Created {filename}{_RESET}')
        print(f'  Run with: {_CYAN}grynk run {filename}{_RESET}')
        sys.exit(0)

    # grynk run <file>  OR  grynk <file>
    filepath = None
    if cmd == 'run':
        if len(args) < 2:
            print(f'{_RED}✖ Usage: grynk run <file.grk>{_RESET}')
            sys.exit(1)
        filepath = args[1]
    elif cmd.endswith('.grk') or (len(args) >= 1 and os.path.isfile(cmd)):
        filepath = cmd
    else:
        print(f'{_RED}✖ Unknown command: {cmd!r}{_RESET}')
        print(f'  Run {_BOLD}grynk help{_RESET} for usage.')
        sys.exit(1)

    # Run the file
    if not os.path.isfile(filepath):
        print(f'{_RED}✖ File not found: {filepath!r}{_RESET}')
        sys.exit(1)

    if not filepath.endswith('.grk'):
        print(f'{_YELLOW}⚠ Warning: file does not have .grk extension{_RESET}')

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
    except IOError as e:
        print(f'{_RED}✖ Cannot read file: {e}{_RESET}')
        sys.exit(1)

    # Execute
    try:
        from grynk_core.lexer import tokenize
        from grynk_core.parser import parse
        from grynk_core.interpreter import Interpreter
        from grynk_core.errors import GrynkError, grynk_exit_error

        tokens = tokenize(source, filepath)
        ast = parse(tokens, source)
        interp = Interpreter()
        interp.run(ast)

    except GrynkError as e:
        print(e.display(), file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print(f'\n{_YELLOW}Interrupted.{_RESET}')
        sys.exit(130)
    except Exception as e:
        print(f'{_RED}✖ Grynk Internal Error: {e}{_RESET}', file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
