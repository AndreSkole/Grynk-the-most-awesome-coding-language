"""Grynk Lexer — tokenizes .grk source into a stream of tokens."""

import re
from .errors import GrynkParseError

# ── Token types ──────────────────────────────────────────────────────────────
TT = type('TT', (), {
    # Literals
    'INT': 'INT', 'FLOAT': 'FLOAT', 'STRING': 'STRING',
    'BOOL': 'BOOL', 'NULL': 'NULL',
    # Identifiers / keywords
    'IDENT': 'IDENT', 'KEYWORD': 'KEYWORD',
    # Operators
    'PLUS': 'PLUS', 'MINUS': 'MINUS', 'STAR': 'STAR', 'SLASH': 'SLASH',
    'PERCENT': 'PERCENT', 'POWER': 'POWER',
    'EQ': 'EQ', 'NEQ': 'NEQ', 'LT': 'LT', 'GT': 'GT',
    'LTE': 'LTE', 'GTE': 'GTE',
    'AND': 'AND', 'OR': 'OR', 'NOT': 'NOT',
    'ASSIGN': 'ASSIGN', 'PLUS_ASSIGN': 'PLUS_ASSIGN', 'MINUS_ASSIGN': 'MINUS_ASSIGN',
    'PIPE': 'PIPE',
    # Punctuation
    'LPAREN': 'LPAREN', 'RPAREN': 'RPAREN',
    'LBRACE': 'LBRACE', 'RBRACE': 'RBRACE',
    'LBRACKET': 'LBRACKET', 'RBRACKET': 'RBRACKET',
    'COMMA': 'COMMA', 'DOT': 'DOT', 'COLON': 'COLON',
    'NEWLINE': 'NEWLINE', 'EOF': 'EOF',
})()

KEYWORDS = {
    'let', 'mut', 'fn', 'return',
    'if', 'elif', 'else',
    'loop', 'times', 'for', 'in', 'while', 'break', 'continue',
    'try', 'catch', 'throw',
    'match', 'case',
    'say', 'ask',
    'true', 'false', 'null',
    'and', 'or', 'not',
}


class Token:
    __slots__ = ('type', 'value', 'line')

    def __init__(self, type_, value, line):
        self.type = type_
        self.value = value
        self.line = line

    def __repr__(self):
        return f'Token({self.type}, {self.value!r}, line={self.line})'


class Lexer:
    def __init__(self, source, filename='<unknown>'):
        self.source = source
        self.filename = filename
        self.pos = 0
        self.line = 1
        self.tokens = []

    # ── helpers ──────────────────────────────────────────────────────────────

    def peek(self, offset=0):
        idx = self.pos + offset
        return self.source[idx] if idx < len(self.source) else '\0'

    def advance(self):
        ch = self.source[self.pos]
        self.pos += 1
        if ch == '\n':
            self.line += 1
        return ch

    def match(self, expected):
        if self.pos < len(self.source) and self.source[self.pos] == expected:
            self.pos += 1
            return True
        return False

    def skip_whitespace_and_comments(self):
        while self.pos < len(self.source):
            ch = self.source[self.pos]
            if ch in (' ', '\t', '\r'):
                self.pos += 1
            elif ch == '#':
                # comment: skip to end of line
                while self.pos < len(self.source) and self.source[self.pos] != '\n':
                    self.pos += 1
            else:
                break

    def add(self, type_, value):
        self.tokens.append(Token(type_, value, self.line))

    # ── string lexing with {interpolation} ───────────────────────────────────

    def lex_string(self, quote):
        """Lex a quoted string and expand {expr} interpolations."""
        line = self.line
        parts = []     # list of ('lit', str) or ('interp', str)
        buf = []

        while self.pos < len(self.source):
            ch = self.source[self.pos]

            if ch == quote:
                self.pos += 1
                break
            elif ch == '\n':
                raise GrynkParseError("Unterminated string literal", line=self.line)
            elif ch == '\\':
                self.pos += 1
                esc = self.advance()
                esc_map = {'n': '\n', 't': '\t', 'r': '\r', '\\': '\\',
                           '"': '"', "'": "'", '{': '{', '}': '}'}
                buf.append(esc_map.get(esc, esc))
            elif ch == '{':
                # flush literal buffer
                if buf:
                    parts.append(('lit', ''.join(buf)))
                    buf = []
                self.pos += 1
                # check for escaped {{
                if self.pos < len(self.source) and self.source[self.pos] == '{':
                    buf.append('{')
                    self.pos += 1
                    continue
                # collect interpolation expression up to matching }
                depth = 1
                expr_buf = []
                while self.pos < len(self.source) and depth > 0:
                    c2 = self.source[self.pos]
                    self.pos += 1
                    if c2 == '{':
                        depth += 1
                        expr_buf.append(c2)
                    elif c2 == '}':
                        depth -= 1
                        if depth > 0:
                            expr_buf.append(c2)
                    else:
                        expr_buf.append(c2)
                parts.append(('interp', ''.join(expr_buf).strip()))
            else:
                buf.append(ch)
                self.pos += 1

        if buf:
            parts.append(('lit', ''.join(buf)))

        # Build value: list of ('lit', s) | ('interp', code_string)
        # The interpreter will handle concatenation
        self.tokens.append(Token(TT.STRING, parts, line))

    # ── number lexing ─────────────────────────────────────────────────────────

    def lex_number(self):
        line = self.line
        start = self.pos
        is_float = False
        while self.pos < len(self.source) and (self.source[self.pos].isdigit()):
            self.pos += 1
        if self.pos < len(self.source) and self.source[self.pos] == '.' and \
                self.pos + 1 < len(self.source) and self.source[self.pos + 1].isdigit():
            is_float = True
            self.pos += 1
            while self.pos < len(self.source) and self.source[self.pos].isdigit():
                self.pos += 1
        raw = self.source[start:self.pos]
        if is_float:
            self.tokens.append(Token(TT.FLOAT, float(raw), line))
        else:
            self.tokens.append(Token(TT.INT, int(raw), line))

    # ── identifier / keyword lexing ───────────────────────────────────────────

    def lex_ident(self):
        line = self.line
        start = self.pos
        while self.pos < len(self.source) and (self.source[self.pos].isalnum() or self.source[self.pos] == '_'):
            self.pos += 1
        word = self.source[start:self.pos]
        if word in ('true', 'false'):
            self.tokens.append(Token(TT.BOOL, word == 'true', line))
        elif word == 'null':
            self.tokens.append(Token(TT.NULL, None, line))
        elif word == 'and':
            self.tokens.append(Token(TT.AND, 'and', line))
        elif word == 'or':
            self.tokens.append(Token(TT.OR, 'or', line))
        elif word == 'not':
            self.tokens.append(Token(TT.NOT, 'not', line))
        elif word in KEYWORDS:
            self.tokens.append(Token(TT.KEYWORD, word, line))
        else:
            self.tokens.append(Token(TT.IDENT, word, line))

    # ── main tokenize ─────────────────────────────────────────────────────────

    def tokenize(self):
        source = self.source

        # Collapse multiple blank newlines but keep logical newlines
        last_was_newline = True   # suppress leading newlines

        while self.pos < len(source):
            self.skip_whitespace_and_comments()
            if self.pos >= len(source):
                break

            ch = source[self.pos]
            line = self.line

            # Newline
            if ch == '\n':
                self.pos += 1
                self.line += 1
                if not last_was_newline:
                    self.add(TT.NEWLINE, '\n')
                    last_was_newline = True
                continue
            last_was_newline = False

            # String literals
            if ch in ('"', "'"):
                self.pos += 1
                self.lex_string(ch)
                continue

            # Numbers
            if ch.isdigit():
                self.lex_number()
                continue

            # Identifiers / keywords
            if ch.isalpha() or ch == '_':
                self.lex_ident()
                continue

            # Two-char operators
            if ch == '|' and self.peek(1) == '>':
                self.pos += 2
                self.add(TT.PIPE, '|>')
                continue
            if ch == '*' and self.peek(1) == '*':
                self.pos += 2
                self.add(TT.POWER, '**')
                continue
            if ch == '+' and self.peek(1) == '=':
                self.pos += 2
                self.add(TT.PLUS_ASSIGN, '+=')
                continue
            if ch == '-' and self.peek(1) == '=':
                self.pos += 2
                self.add(TT.MINUS_ASSIGN, '-=')
                continue
            if ch == '=' and self.peek(1) == '=':
                self.pos += 2
                self.add(TT.EQ, '==')
                continue
            if ch == '!' and self.peek(1) == '=':
                self.pos += 2
                self.add(TT.NEQ, '!=')
                continue
            if ch == '<' and self.peek(1) == '=':
                self.pos += 2
                self.add(TT.LTE, '<=')
                continue
            if ch == '>' and self.peek(1) == '=':
                self.pos += 2
                self.add(TT.GTE, '>=')
                continue
            if ch == '&' and self.peek(1) == '&':
                self.pos += 2
                self.add(TT.AND, '&&')
                continue
            if ch == '|' and self.peek(1) == '|':
                self.pos += 2
                self.add(TT.OR, '||')
                continue

            # Single-char operators / punctuation
            single = {
                '+': TT.PLUS, '-': TT.MINUS, '*': TT.STAR, '/': TT.SLASH,
                '%': TT.PERCENT, '=': TT.ASSIGN, '<': TT.LT, '>': TT.GT,
                '!': TT.NOT,
                '(': TT.LPAREN, ')': TT.RPAREN,
                '{': TT.LBRACE, '}': TT.RBRACE,
                '[': TT.LBRACKET, ']': TT.RBRACKET,
                ',': TT.COMMA, '.': TT.DOT, ':': TT.COLON,
            }
            if ch in single:
                self.pos += 1
                self.add(single[ch], ch)
                continue

            raise GrynkParseError(f"Unexpected character '{ch}'", line=self.line)

        self.add(TT.EOF, None)
        return self.tokens


def tokenize(source, filename='<unknown>'):
    return Lexer(source, filename).tokenize()
