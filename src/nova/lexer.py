import re
from enum import Enum, auto
from dataclasses import dataclass

class TokenType(Enum):
    # Keywords
    LET = auto()
    CONST = auto()
    FN = auto()
    CLASS = auto()
    MODEL = auto()
    IF = auto()
    ELSE = auto()
    FOR = auto()
    PARALLEL = auto()
    IN = auto()
    WHILE = auto()
    TRY = auto()
    CATCH = auto()
    FINALLY = auto()
    RETURN = auto()
    IMPORT = auto()
    FROM = auto()
    EXPORT = auto()
    ASYNC = auto()
    AWAIT = auto()
    MATCH = auto()
    CASE = auto()
    TRAIN = auto()
    LAZY = auto()

    # Literals
    IDENTIFIER = auto()
    INTEGER = auto()
    FLOAT = auto()
    STRING = auto()
    BOOLEAN = auto()
    NULL = auto()

    # Operators
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    PERCENT = auto()
    POWER = auto()
    ASSIGN = auto()
    EQ = auto()
    NE = auto()
    LT = auto()
    GT = auto()
    LE = auto()
    GE = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    PIPELINE = auto()
    SAFE_NAV = auto()
    NULL_COALESCE = auto()
    RANGE = auto()

    # Delimiters
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    COMMA = auto()
    COLON = auto()
    DOT = auto()
    SEMICOLON = auto()
    ARROW = auto() # =>

    EOF = auto()

@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    column: int

class Lexer:
    KEYWORDS = {
        "let": TokenType.LET,
        "const": TokenType.CONST,
        "fn": TokenType.FN,
        "class": TokenType.CLASS,
        "model": TokenType.MODEL,
        "if": TokenType.IF,
        "else": TokenType.ELSE,
        "for": TokenType.FOR,
        "parallel": TokenType.PARALLEL,
        "in": TokenType.IN,
        "while": TokenType.WHILE,
        "try": TokenType.TRY,
        "catch": TokenType.CATCH,
        "finally": TokenType.FINALLY,
        "return": TokenType.RETURN,
        "import": TokenType.IMPORT,
        "from": TokenType.FROM,
        "export": TokenType.EXPORT,
        "async": TokenType.ASYNC,
        "await": TokenType.AWAIT,
        "match": TokenType.MATCH,
        "case": TokenType.CASE,
        "train": TokenType.TRAIN,
        "lazy": TokenType.LAZY,
        "true": TokenType.BOOLEAN,
        "false": TokenType.BOOLEAN,
        "null": TokenType.NULL,
    }

    TOKEN_SPEC = [
        ('FLOAT',     r'\d+\.\d+'),
        ('INTEGER',   r'\d+'),
        ('STRING',    r'"[^"]*"'),
        ('SAFE_NAV',  r'\?\.'),
        ('NULL_COALESCE', r'\?\?'),
        ('PIPELINE',  r'\|>'),
        ('ARROW',     r'=>'),
        ('RANGE',     r'\.\.'),
        ('EQ',        r'=='),
        ('NE',        r'!='),
        ('LE',        r'<='),
        ('GE',        r'>='),
        ('AND',       r'&&'),
        ('OR',        r'\|\|'),
        ('IDENTIFIER',r'[a-zA-Z_][a-zA-Z0-9_]*'),
        ('PLUS',      r'\+'),
        ('MINUS',     r'-'),
        ('STAR',      r'\*'),
        ('COMMENT',   r'//.*'),
        ('SLASH',     r'/'),
        ('PERCENT',   r'%'),
        ('POWER',     r'\*\*'),
        ('ASSIGN',    r'='),
        ('LT',        r'<'),
        ('GT',        r'>'),
        ('NOT',       r'!'),
        ('LPAREN',    r'\('),
        ('RPAREN',    r'\)'),
        ('LBRACE',    r'\{'),
        ('RBRACE',    r'\}'),
        ('LBRACKET',  r'\['),
        ('RBRACKET',  r'\]'),
        ('COMMA',     r','),
        ('COLON',     r':'),
        ('DOT',       r'\.'),
        ('SEMICOLON', r';'),
        ('NEWLINE',   r'\n'),
        ('SKIP',      r'[ \t\r]+'),
        ('MISMATCH',  r'.'),
    ]

    def __init__(self, source: str):
        self.source = source
        self.tokens = []
        self.line = 1
        self.column_start = 0

    def tokenize(self):
        tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in self.TOKEN_SPEC)
        for mo in re.finditer(tok_regex, self.source):
            kind = mo.lastgroup
            value = mo.group()
            column = mo.start() - self.column_start + 1
            if kind == 'FLOAT':
                self.tokens.append(Token(TokenType.FLOAT, value, self.line, column))
            elif kind == 'INTEGER':
                self.tokens.append(Token(TokenType.INTEGER, value, self.line, column))
            elif kind == 'STRING':
                self.tokens.append(Token(TokenType.STRING, value[1:-1], self.line, column))
            elif kind == 'IDENTIFIER':
                type = self.KEYWORDS.get(value, TokenType.IDENTIFIER)
                self.tokens.append(Token(type, value, self.line, column))
            elif kind == 'NEWLINE':
                self.line += 1
                self.column_start = mo.end()
            elif kind == 'SKIP' or kind == 'COMMENT':
                pass
            elif kind == 'MISMATCH':
                raise RuntimeError(f'{value!r} unexpected on line {self.line}')
            else:
                type = getattr(TokenType, kind)
                self.tokens.append(Token(type, value, self.line, column))

        self.tokens.append(Token(TokenType.EOF, "", self.line, len(self.source) - self.column_start + 1))
        return self.tokens
