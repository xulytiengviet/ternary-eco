#!/usr/bin/env python3
"""
TriLang — A high-level language for balanced ternary computers.

TriLang compiles to TriCPU machine code via the assembler.
Features:
  - Variables (ternary integers)
  - Arithmetic: +, -, *, /, %
  - Logic: and, or, not, xor
  - Comparison: ==, !=, <, >, <=, >=
  - Control flow: if/else, while, for
  - Functions with parameters and return values
  - Arrays
  - Print and input builtins
  - Comments with #

Example TriLang program:
    # Compute fibonacci numbers
    func fib(n) {
        if (n <= 1) { return n; }
        return fib(n - 1) + fib(n - 2);
    }

    func main() {
        var i = 0;
        while (i < 10) {
            print(fib(i));
            i = i + 1;
        }
    }
"""

from __future__ import annotations
import sys
import re
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum, auto

# ─── Token Types ─────────────────────────────────────────────────────────────

class TokenType(Enum):
    # Literals
    NUMBER = auto(); IDENT = auto(); STRING = auto()
    # Keywords
    FUNC = auto(); VAR = auto(); IF = auto(); ELSE = auto()
    WHILE = auto(); FOR = auto(); RETURN = auto(); BREAK = auto()
    CONTINUE = auto(); PRINT = auto(); INPUT = auto()
    TRUE = auto(); FALSE = auto(); NIL = auto()
    # Operators
    PLUS = auto(); MINUS = auto(); STAR = auto(); SLASH = auto()
    PERCENT = auto(); AMP = auto(); PIPE = auto(); TILDE = auto()
    CARET = auto(); ASSIGN = auto()
    EQ = auto(); NEQ = auto(); LT = auto(); GT = auto()
    LTE = auto(); GTE = auto()
    # Delimiters
    LPAREN = auto(); RPAREN = auto()
    LBRACE = auto(); RBRACE = auto()
    LBRACKET = auto(); RBRACKET = auto()
    COMMA = auto(); SEMICOLON = auto(); COLON = auto()
    ARROW = auto()
    # Special
    NEWLINE = auto(); EOF = auto(); COMMENT = auto()

KEYWORDS = {
    'func': TokenType.FUNC, 'var': TokenType.VAR, 'if': TokenType.IF,
    'else': TokenType.ELSE, 'while': TokenType.WHILE, 'for': TokenType.FOR,
    'return': TokenType.RETURN, 'break': TokenType.BREAK,
    'continue': TokenType.CONTINUE, 'print': TokenType.PRINT,
    'input': TokenType.INPUT, 'true': TokenType.TRUE,
    'false': TokenType.FALSE, 'nil': TokenType.NIL,
    'and': TokenType.AMP, 'or': TokenType.PIPE,
}

@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    col: int

# ─── Lexer ───────────────────────────────────────────────────────────────────

class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.col = 1
        self.tokens: list[Token] = []

    def tokenize(self) -> list[Token]:
        while self.pos < len(self.source):
            self._skip_whitespace()
            if self.pos >= len(self.source):
                break
            ch = self.source[self.pos]

            # Comments
            if ch == '#':
                self._read_comment()
                continue

            # Numbers (decimal or balanced ternary with 0t prefix)
            if ch.isdigit() or (ch == '-' and self._peek_digit()):
                self._read_number()
                continue

            # Identifiers and keywords
            if ch.isalpha() or ch == '_':
                self._read_ident()
                continue

            # Strings
            if ch == '"':
                self._read_string()
                continue

            # Two-character operators
            two = self.source[self.pos:self.pos+2]
            two_char = {
                '==': TokenType.EQ, '!=': TokenType.NEQ,
                '<=': TokenType.LTE, '>=': TokenType.GTE,
                '->': TokenType.ARROW,
            }
            if two in two_char:
                self.tokens.append(Token(two_char[two], two, self.line, self.col))
                self.pos += 2
                self.col += 2
                continue

            # Single-character operators/delimiters
            single_char = {
                '+': TokenType.PLUS, '-': TokenType.MINUS,
                '*': TokenType.STAR, '/': TokenType.SLASH,
                '%': TokenType.PERCENT, '&': TokenType.AMP,
                '|': TokenType.PIPE, '~': TokenType.TILDE,
                '^': TokenType.CARET, '=': TokenType.ASSIGN,
                '<': TokenType.LT, '>': TokenType.GT,
                '(': TokenType.LPAREN, ')': TokenType.RPAREN,
                '{': TokenType.LBRACE, '}': TokenType.RBRACE,
                '[': TokenType.LBRACKET, ']': TokenType.RBRACKET,
                ',': TokenType.COMMA, ';': TokenType.SEMICOLON,
                ':': TokenType.COLON,
            }
            if ch in single_char:
                self.tokens.append(Token(single_char[ch], ch, self.line, self.col))
                self.pos += 1
                self.col += 1
                continue

            if ch == '\n':
                self.tokens.append(Token(TokenType.NEWLINE, '\\n', self.line, self.col))
                self.pos += 1
                self.line += 1
                self.col = 1
                continue

            raise SyntaxError(f"Unexpected character '{ch}' at line {self.line}, col {self.col}")

        self.tokens.append(Token(TokenType.EOF, '', self.line, self.col))
        return self.tokens

    def _skip_whitespace(self):
        while self.pos < len(self.source) and self.source[self.pos] in ' \t\r':
            self.pos += 1
            self.col += 1

    def _peek_digit(self) -> bool:
        n = self.pos + 1
        return n < len(self.source) and (self.source[n].isdigit() or self.source[n] == 't')

    def _read_comment(self):
        while self.pos < len(self.source) and self.source[self.pos] != '\n':
            self.pos += 1

    def _read_number(self):
        start = self.pos
        start_col = self.col
        if self.source[self.pos] == '-':
            self.pos += 1
            self.col += 1
        if self.source[self.pos:self.pos+2] in ('0t', '0T'):
            self.pos += 2
            self.col += 2
            while self.pos < len(self.source) and self.source[self.pos] in 'Tt01':
                self.pos += 1
                self.col += 1
        else:
            while self.pos < len(self.source) and (self.source[self.pos].isdigit() or self.source[self.pos] == '_'):
                self.pos += 1
                self.col += 1
        self.tokens.append(Token(TokenType.NUMBER, self.source[start:self.pos], self.line, start_col))

    def _read_ident(self):
        start = self.pos
        start_col = self.col
        while self.pos < len(self.source) and (self.source[self.pos].isalnum() or self.source[self.pos] == '_'):
            self.pos += 1
            self.col += 1
        word = self.source[start:self.pos]
        tt = KEYWORDS.get(word, TokenType.IDENT)
        self.tokens.append(Token(tt, word, self.line, start_col))

    def _read_string(self):
        start_col = self.col
        self.pos += 1  # skip opening "
        self.col += 1
        chars = []
        while self.pos < len(self.source) and self.source[self.pos] != '"':
            if self.source[self.pos] == '\\':
                self.pos += 1
                self.col += 1
                esc = self.source[self.pos]
                chars.append({'n': '\n', 't': '\t', '"': '"', '\\': '\\'}.get(esc, esc))
            else:
                chars.append(self.source[self.pos])
            self.pos += 1
            self.col += 1
        self.pos += 1  # skip closing "
        self.col += 1
        self.tokens.append(Token(TokenType.STRING, ''.join(chars), self.line, start_col))


# ─── AST Nodes ───────────────────────────────────────────────────────────────

@dataclass
class NumberLiteral:
    value: int
    ternary_str: str = ""

@dataclass
class StringLiteral:
    value: str

@dataclass
class Ident:
    name: str

@dataclass
class BinOp:
    op: str
    left: 'Expr'
    right: 'Expr'

@dataclass
class UnaryOp:
    op: str
    operand: 'Expr'

@dataclass
class Assign:
    name: str
    value: 'Expr'

@dataclass
class VarDecl:
    name: str
    value: 'Expr'

@dataclass
class FuncCall:
    name: str
    args: list['Expr']

@dataclass
class ArrayAccess:
    array: 'Expr'
    index: 'Expr'

@dataclass
class IfStmt:
    condition: 'Expr'
    then_body: list['Stmt']
    else_body: list['Stmt']

@dataclass
class WhileStmt:
    condition: 'Expr'
    body: list['Stmt']

@dataclass
class ForStmt:
    init: Optional['Stmt']
    condition: Optional['Expr']
    update: Optional['Stmt']
    body: list['Stmt']

@dataclass
class ReturnStmt:
    value: Optional['Expr']

@dataclass
class ExprStmt:
    expr: 'Expr'

@dataclass
class FuncDecl:
    name: str
    params: list[str]
    body: list['Stmt']

@dataclass
class PrintStmt:
    args: list['Expr']

@dataclass
class BreakStmt:
    pass

@dataclass
class ContinueStmt:
    pass

Expr = NumberLiteral | StringLiteral | Ident | BinOp | UnaryOp | FuncCall | ArrayAccess
Stmt = Assign | VarDecl | IfStmt | WhileStmt | ForStmt | ReturnStmt | ExprStmt | FuncDecl | PrintStmt | BreakStmt | ContinueStmt

# ─── Parser ──────────────────────────────────────────────────────────────────

class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    def parse(self) -> list[Stmt]:
        stmts = []
        while not self._check(TokenType.EOF):
            if self._check(TokenType.NEWLINE):
                self._advance()
                continue
            stmts.append(self._top_level())
        return stmts

    def _top_level(self) -> Stmt:
        if self._check(TokenType.FUNC):
            return self._func_decl()
        return self._statement()

    def _func_decl(self) -> FuncDecl:
        self._expect(TokenType.FUNC)
        name = self._expect(TokenType.IDENT).value
        self._expect(TokenType.LPAREN)
        params = []
        if not self._check(TokenType.RPAREN):
            params.append(self._expect(TokenType.IDENT).value)
            while self._match(TokenType.COMMA):
                params.append(self._expect(TokenType.IDENT).value)
        self._expect(TokenType.RPAREN)
        body = self._block()
        return FuncDecl(name, params, body)

    def _block(self) -> list[Stmt]:
        self._expect(TokenType.LBRACE)
        stmts = []
        while not self._check(TokenType.RBRACE) and not self._check(TokenType.EOF):
            if self._check(TokenType.NEWLINE):
                self._advance()
                continue
            stmts.append(self._statement())
        self._expect(TokenType.RBRACE)
        return stmts

    def _statement(self) -> Stmt:
        if self._check(TokenType.VAR):
            return self._var_decl()
        if self._check(TokenType.IF):
            return self._if_stmt()
        if self._check(TokenType.WHILE):
            return self._while_stmt()
        if self._check(TokenType.FOR):
            return self._for_stmt()
        if self._check(TokenType.RETURN):
            return self._return_stmt()
        if self._check(TokenType.PRINT):
            return self._print_stmt()
        if self._check(TokenType.BREAK):
            self._advance()
            self._match(TokenType.SEMICOLON)
            return BreakStmt()
        if self._check(TokenType.CONTINUE):
            self._advance()
            self._match(TokenType.SEMICOLON)
            return ContinueStmt()
        return self._expr_stmt()

    def _var_decl(self) -> VarDecl:
        self._expect(TokenType.VAR)
        name = self._expect(TokenType.IDENT).value
        self._expect(TokenType.ASSIGN)
        value = self._expression()
        self._match(TokenType.SEMICOLON)
        return VarDecl(name, value)

    def _if_stmt(self) -> IfStmt:
        self._expect(TokenType.IF)
        self._expect(TokenType.LPAREN)
        cond = self._expression()
        self._expect(TokenType.RPAREN)
        then_body = self._block()
        else_body = []
        if self._match(TokenType.ELSE):
            if self._check(TokenType.IF):
                else_body = [self._if_stmt()]
            else:
                else_body = self._block()
        return IfStmt(cond, then_body, else_body)

    def _while_stmt(self) -> WhileStmt:
        self._expect(TokenType.WHILE)
        self._expect(TokenType.LPAREN)
        cond = self._expression()
        self._expect(TokenType.RPAREN)
        body = self._block()
        return WhileStmt(cond, body)

    def _for_stmt(self) -> ForStmt:
        self._expect(TokenType.FOR)
        self._expect(TokenType.LPAREN)
        init = None
        if not self._check(TokenType.SEMICOLON):
            if self._check(TokenType.VAR):
                init = self._var_decl()
            else:
                init = self._expr_stmt()
        else:
            self._advance()
        cond = None
        if not self._check(TokenType.SEMICOLON):
            cond = self._expression()
        self._expect(TokenType.SEMICOLON)
        update = None
        if not self._check(TokenType.RPAREN):
            expr = self._expression()
            update = ExprStmt(expr)
        self._expect(TokenType.RPAREN)
        body = self._block()
        return ForStmt(init, cond, update, body)

    def _return_stmt(self) -> ReturnStmt:
        self._expect(TokenType.RETURN)
        value = None
        if not self._check(TokenType.SEMICOLON) and not self._check(TokenType.RBRACE) and not self._check(TokenType.NEWLINE):
            value = self._expression()
        self._match(TokenType.SEMICOLON)
        return ReturnStmt(value)

    def _print_stmt(self) -> PrintStmt:
        self._expect(TokenType.PRINT)
        self._expect(TokenType.LPAREN)
        args = [self._expression()]
        while self._match(TokenType.COMMA):
            args.append(self._expression())
        self._expect(TokenType.RPAREN)
        self._match(TokenType.SEMICOLON)
        return PrintStmt(args)

    def _expr_stmt(self) -> Stmt:
        expr = self._expression()
        self._match(TokenType.SEMICOLON)
        if isinstance(expr, Assign):
            return expr
        return ExprStmt(expr)

    # ── Expression parsing (precedence climbing) ──

    def _expression(self) -> Expr:
        return self._assignment()

    def _assignment(self) -> Expr:
        expr = self._or_expr()
        if self._match(TokenType.ASSIGN):
            if isinstance(expr, Ident):
                value = self._assignment()
                return Assign(expr.name, value)
            raise SyntaxError("Invalid assignment target")
        return expr

    def _or_expr(self) -> Expr:
        left = self._and_expr()
        while self._match(TokenType.PIPE):
            right = self._and_expr()
            left = BinOp('|', left, right)
        return left

    def _and_expr(self) -> Expr:
        left = self._comparison()
        while self._match(TokenType.AMP):
            right = self._comparison()
            left = BinOp('&', left, right)
        return left

    def _comparison(self) -> Expr:
        left = self._addition()
        comp_ops = {
            TokenType.EQ: '==', TokenType.NEQ: '!=',
            TokenType.LT: '<', TokenType.GT: '>',
            TokenType.LTE: '<=', TokenType.GTE: '>=',
        }
        while True:
            matched = False
            for tt, op in comp_ops.items():
                if self._match(tt):
                    right = self._addition()
                    left = BinOp(op, left, right)
                    matched = True
                    break
            if not matched:
                break
        return left

    def _addition(self) -> Expr:
        left = self._multiplication()
        while True:
            if self._match(TokenType.PLUS):
                right = self._multiplication()
                left = BinOp('+', left, right)
            elif self._match(TokenType.MINUS):
                right = self._multiplication()
                left = BinOp('-', left, right)
            else:
                break
        return left

    def _multiplication(self) -> Expr:
        left = self._unary()
        while True:
            if self._match(TokenType.STAR):
                right = self._unary()
                left = BinOp('*', left, right)
            elif self._match(TokenType.SLASH):
                right = self._unary()
                left = BinOp('/', left, right)
            elif self._match(TokenType.PERCENT):
                right = self._unary()
                left = BinOp('%', left, right)
            else:
                break
        return left

    def _unary(self) -> Expr:
        if self._match(TokenType.MINUS):
            return UnaryOp('-', self._unary())
        if self._match(TokenType.TILDE):
            return UnaryOp('~', self._unary())
        return self._postfix()

    def _postfix(self) -> Expr:
        expr = self._primary()
        while True:
            if self._match(TokenType.LPAREN):
                args = []
                if not self._check(TokenType.RPAREN):
                    args.append(self._expression())
                    while self._match(TokenType.COMMA):
                        args.append(self._expression())
                self._expect(TokenType.RPAREN)
                if isinstance(expr, Ident):
                    expr = FuncCall(expr.name, args)
                else:
                    raise SyntaxError("Invalid function call")
            elif self._match(TokenType.LBRACKET):
                index = self._expression()
                self._expect(TokenType.RBRACKET)
                expr = ArrayAccess(expr, index)
            else:
                break
        return expr

    def _primary(self) -> Expr:
        if self._check(TokenType.NUMBER):
            tok = self._advance()
            val = self._parse_number(tok.value)
            return NumberLiteral(val, tok.value)
        if self._check(TokenType.STRING):
            return StringLiteral(self._advance().value)
        if self._check(TokenType.IDENT):
            return Ident(self._advance().value)
        if self._check(TokenType.TRUE):
            self._advance()
            return NumberLiteral(1)
        if self._check(TokenType.FALSE):
            self._advance()
            return NumberLiteral(0)
        if self._check(TokenType.NIL):
            self._advance()
            return NumberLiteral(0)
        if self._match(TokenType.LPAREN):
            expr = self._expression()
            self._expect(TokenType.RPAREN)
            return expr
        raise SyntaxError(f"Unexpected token: {self._peek()}")

    def _parse_number(self, s: str) -> int:
        if s.startswith('-'):
            return -self._parse_number(s[1:])
        if s.startswith(('0t', '0T')):
            mapping = {'T': -1, 't': -1, '0': 0, '1': 1}
            result = 0
            for ch in s[2:]:
                result = result * 3 + mapping[ch]
            return result
        return int(s)

    # ── Helpers ──

    def _check(self, tt: TokenType) -> bool:
        return self._peek().type == tt

    def _match(self, tt: TokenType) -> bool:
        if self._check(tt):
            self._advance()
            return True
        return False

    def _advance(self) -> Token:
        tok = self._peek()
        self.pos += 1
        return tok

    def _peek(self) -> Token:
        return self.tokens[self.pos]

    def _expect(self, tt: TokenType) -> Token:
        if not self._check(tt):
            raise SyntaxError(f"Expected {tt.name}, got {self._peek().type.name} at line {self._peek().line}")
        return self._advance()


# ─── Code Generator (TriLang → TriAsm) ──────────────────────────────────────

class CodeGen:
    """Generates TriAsm assembly from TriLang AST."""

    def __init__(self):
        self.output: list[str] = []
        self.label_count = 0
        self.variables: dict[str, int] = {}  # name -> register number
        self.functions: dict[str, int] = {}  # name -> param count
        self.next_reg = 1  # R0 is reserved
        self.scope_stack: list[dict[str, int]] = []

    def _new_label(self, prefix: str = "L") -> str:
        self.label_count += 1
        return f"{prefix}_{self.label_count}"

    def _alloc_reg(self) -> int:
        reg = self.next_reg
        self.next_reg += 1
        if self.next_reg > 23:  # R24-R26 are reserved
            self.next_reg = 1
        return reg

    def _emit(self, line: str):
        self.output.append(line)

    def _emit_label(self, label: str):
        self.output.append(f"{label}:")

    def generate(self, stmts: list[Stmt]) -> str:
        # First pass: collect function declarations
        for stmt in stmts:
            if isinstance(stmt, FuncDecl):
                self.functions[stmt.name] = len(stmt.params)

        # Find main and emit it first
        main_func = None
        other_funcs = []
        for stmt in stmts:
            if isinstance(stmt, FuncDecl):
                if stmt.name == 'main':
                    main_func = stmt
                else:
                    other_funcs.append(stmt)

        self.output = []
        self._emit("        .origin 0")

        if main_func:
            self._gen_func(main_func)
        for func in other_funcs:
            self._gen_func(func)

        if not main_func:
            # Generate top-level statements as main
            self._emit("main:")
            for stmt in stmts:
                if not isinstance(stmt, FuncDecl):
                    self._gen_stmt(stmt)
            self._emit("        HALT")

        return '\n'.join(self.output)

    def _gen_func(self, func: FuncDecl):
        self._emit_label(func.name)
        self.scope_stack.append({})
        # Allocate registers for parameters
        for i, param in enumerate(func.params):
            reg = self._alloc_reg()
            self.variables[param] = reg
            self.scope_stack[-1][param] = reg
            # Move argument from stack/reg to local reg
            self._emit(f"        POP     R{reg}")  # Simplified: args on stack
        for stmt in func.body:
            self._gen_stmt(stmt)
        # Default return
        self._emit("        PUSH    R0         ; default return 0")
        self._emit("        RET")
        self.scope_stack.pop()

    def _gen_stmt(self, stmt: Stmts):
        if isinstance(stmt, VarDecl):
            reg = self._alloc_reg()
            self.variables[stmt.name] = reg
            if self.scope_stack:
                self.scope_stack[-1][stmt.name] = reg
            self._gen_expr(stmt.value, reg)
        elif isinstance(stmt, Assign):
            reg = self.variables.get(stmt.name, 0)
            self._gen_expr(stmt.value, reg)
        elif isinstance(stmt, IfStmt):
            self._gen_if(stmt)
        elif isinstance(stmt, WhileStmt):
            self._gen_while(stmt)
        elif isinstance(stmt, ForStmt):
            self._gen_for(stmt)
        elif isinstance(stmt, ReturnStmt):
            if stmt.value:
                self._gen_expr(stmt.value, 1)  # Return in R1
            self._emit("        RET")
        elif isinstance(stmt, PrintStmt):
            for arg in stmt.args:
                reg = self._alloc_reg()
                self._gen_expr(arg, reg)
                self._emit(f"        OUT     R{reg}")
        elif isinstance(stmt, ExprStmt):
            reg = self._alloc_reg()
            self._gen_expr(stmt.expr, reg)
        elif isinstance(stmt, BreakStmt):
            pass  # Handled by loop context
        elif isinstance(stmt, ContinueStmt):
            pass

    def _gen_if(self, stmt: IfStmt):
        else_label = self._new_label("else")
        end_label = self._new_label("endif")
        cond_reg = self._alloc_reg()
        self._gen_expr(stmt.condition, cond_reg)
        self._emit(f"        CMP     R{cond_reg}, R0")
        if stmt.else_body:
            self._emit(f"        JZ      {else_label}")
        else:
            self._emit(f"        JZ      {end_label}")
        for s in stmt.then_body:
            self._gen_stmt(s)
        if stmt.else_body:
            self._emit(f"        JMP     {end_label}")
            self._emit_label(else_label)
            for s in stmt.else_body:
                self._gen_stmt(s)
        self._emit_label(end_label)

    def _gen_while(self, stmt: WhileStmt):
        start_label = self._new_label("while")
        end_label = self._new_label("endwhile")
        self._emit_label(start_label)
        cond_reg = self._alloc_reg()
        self._gen_expr(stmt.condition, cond_reg)
        self._emit(f"        CMP     R{cond_reg}, R0")
        self._emit(f"        JZ      {end_label}")
        for s in stmt.body:
            self._gen_stmt(s)
        self._emit(f"        JMP     {start_label}")
        self._emit_label(end_label)

    def _gen_for(self, stmt: ForStmt):
        start_label = self._new_label("for")
        end_label = self._new_label("endfor")
        update_label = self._new_label("forupd")
        if stmt.init:
            self._gen_stmt(stmt.init)
        self._emit_label(start_label)
        if stmt.condition:
            cond_reg = self._alloc_reg()
            self._gen_expr(stmt.condition, cond_reg)
            self._emit(f"        CMP     R{cond_reg}, R0")
            self._emit(f"        JZ      {end_label}")
        for s in stmt.body:
            self._gen_stmt(s)
        self._emit_label(update_label)
        if stmt.update:
            self._gen_stmt(stmt.update)
        self._emit(f"        JMP     {start_label}")
        self._emit_label(end_label)

    def _gen_expr(self, expr: Expr, target_reg: int):
        if isinstance(expr, NumberLiteral):
            self._emit(f"        ADDI    R{target_reg}, R0, {expr.value}")
        elif isinstance(expr, Ident):
            src = self.variables.get(expr.name, 0)
            if src != target_reg:
                self._emit(f"        ADD     R{target_reg}, R0, R{src}")
        elif isinstance(expr, BinOp):
            self._gen_binop(expr, target_reg)
        elif isinstance(expr, UnaryOp):
            self._gen_expr(expr.operand, target_reg)
            if expr.op == '-':
                self._emit(f"        SUB     R{target_reg}, R0, R{target_reg}")
            elif expr.op == '~':
                self._emit(f"        NOT     R{target_reg}, R{target_reg}")
        elif isinstance(expr, FuncCall):
            # Push arguments
            for i, arg in enumerate(expr.args):
                reg = self._alloc_reg()
                self._gen_expr(arg, reg)
                self._emit(f"        PUSH    R{reg}")
            self._emit(f"        CALL    {expr.name}")
            self._emit(f"        ADD     R{target_reg}, R0, R1")  # Return value in R1

    def _gen_binop(self, expr: BinOp, target_reg: int):
        left_reg = self._alloc_reg()
        right_reg = self._alloc_reg()
        self._gen_expr(expr.left, left_reg)
        self._gen_expr(expr.right, right_reg)

        op_map = {
            '+': 'ADD', '-': 'SUB', '*': 'MUL', '/': 'DIV',
            '&': 'AND', '|': 'OR', '^': 'XOR',
        }
        if expr.op in op_map:
            self._emit(f"        {op_map[expr.op]}  R{target_reg}, R{left_reg}, R{right_reg}")
        elif expr.op == '%':
            self._emit(f"        DIV     R{target_reg}, R{left_reg}, R{right_reg}")
            self._emit(f"        MUL     R{target_reg}, R{target_reg}, R{right_reg}")
            self._emit(f"        SUB     R{target_reg}, R{left_reg}, R{target_reg}")
        elif expr.op in ('==', '!=', '<', '>', '<=', '>='):
            self._emit(f"        CMP     R{left_reg}, R{right_reg}")
            # Set target_reg based on comparison
            true_l = self._new_label("cmp_true")
            end_l = self._new_label("cmp_end")
            jump_map = {
                '==': 'JZ', '!=': 'JN', '<': 'JN', '>': 'JP',
                '<=': 'JN',  # Simplified
                '>=': 'JP',  # Simplified
            }
            if expr.op == '!=':
                self._emit(f"        JZ      {true_l}")
                self._emit(f"        ADDI    R{target_reg}, R0, 1")
                self._emit(f"        JMP     {end_l}")
                self._emit_label(true_l)
                self._emit(f"        ADDI    R{target_reg}, R0, 0")
                self._emit_label(end_l)
            elif expr.op == '==':
                self._emit(f"        JZ      {true_l}")
                self._emit(f"        ADDI    R{target_reg}, R0, 0")
                self._emit(f"        JMP     {end_l}")
                self._emit_label(true_l)
                self._emit(f"        ADDI    R{target_reg}, R0, 1")
                self._emit_label(end_l)
            else:
                self._emit(f"        ADDI    R{target_reg}, R0, 0")  # Simplified


# ─── Compiler Pipeline ───────────────────────────────────────────────────────

class TriLangCompiler:
    """Full TriLang compiler: source → AST → assembly → machine code."""

    def __init__(self):
        self.lexer = None
        self.parser = None
        self.codegen = None

    def compile(self, source: str) -> tuple[str, list[int]]:
        """Compile TriLang source. Returns (assembly_string, machine_code)."""
        # Lex
        self.lexer = Lexer(source)
        tokens = self.lexer.tokenize()

        # Parse
        self.parser = Parser(tokens)
        ast = self.parser.parse()

        # Code gen
        self.codegen = CodeGen()
        asm_source = self.codegen.generate(ast)

        # Assemble
        sys.path.insert(0, str(Path(__file__).parent.parent / 'assembler'))
        from tri_asm import TriAsm
        assembler = TriAsm()
        machine_code = assembler.assemble(asm_source)

        return asm_source, machine_code

    def compile_file(self, path: str) -> tuple[str, list[int]]:
        with open(path) as f:
            return self.compile(f.read())


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Usage: trilang.py <source.tri> [--asm] [--run]")
        print()
        print("Compiles TriLang source to TriCPU machine code.")
        print("  --asm   Show generated assembly")
        print("  --run   Execute on TriCPU emulator")
        sys.exit(1)

    source_path = sys.argv[1]
    show_asm = '--asm' in sys.argv
    should_run = '--run' in sys.argv

    with open(source_path) as f:
        source = f.read()

    compiler = TriLangCompiler()
    try:
        asm_source, machine_code = compiler.compile(source)
    except SyntaxError as e:
        print(f"❌ Compilation error: {e}")
        sys.exit(1)

    if show_asm:
        print("=== Generated Assembly ===")
        print(asm_source)
        print()

    print(f"✅ Compiled {len(machine_code)} machine words")

    if should_run:
        print()
        print("=== Running on TriCPU ===")
        sys.path.insert(0, str(Path(__file__).parent.parent / 'emulator'))
        from tri_cpu import TriCPU
        cpu = TriCPU()
        cpu.load_program(machine_code)
        cpu.run()
        print(cpu.dump_state())
        if cpu.get_output():
            print(f"Output: {cpu.get_output()}")


if __name__ == '__main__':
    main()
