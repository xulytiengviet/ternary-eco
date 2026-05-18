#!/usr/bin/env python3
"""
TriAsm — Balanced Ternary Assembler

A two-pass assembler for the TriCPU instruction set.
Supports labels, comments, directives, and immediate values in
balanced ternary (T=-1, 0, 0, 1=1) or decimal.

Syntax:
    LABEL:  INSTRUCTION  OPERANDS     ; comment
    .word   VALUE
    .origin ADDRESS
    .ascii  "string"

Example:
            .origin 0
    start:  ADDI    R1, R0, 5        ; R1 = 5
            ADDI    R2, R0, 1        ; R2 = 1
    loop:   MUL     R3, R2, R1       ; R3 = R2 * R1
            ADD     R2, R0, R3       ; R2 = R3
            SUBI    R1, R1, 1        ; R1--
            CMP     R1, R0           ; compare R1 with 0
            JP      loop             ; if positive, loop
            OUT     R2               ; output result
            HALT
"""

from __future__ import annotations
import sys
import re
from pathlib import Path
from typing import Optional

# ─── Opcodes ─────────────────────────────────────────────────────────────────

OPCODES = {
    'NOP': 0, 'HALT': 1, 'LOAD': 2, 'STORE': 3,
    'ADD': 4, 'SUB': 5, 'MUL': 6, 'DIV': 7,
    'AND': 8, 'OR': 9, 'NOT': 10, 'CMP': 11,
    'JMP': 12, 'JZ': 13, 'JN': 14, 'JP': 15,
    'CALL': 16, 'RET': 17, 'PUSH': 18, 'POP': 19,
    'IN': 20, 'OUT': 21, 'SHL': 22, 'SHR': 23,
    'XOR': 24, 'ADDI': 25, 'SUBI': 26,
}

# Instructions and their operand formats
# R = register, M = memory address, I = immediate
INSTR_FORMATS = {
    'NOP':  (),          'HALT': (),
    'LOAD':  ('R', 'R'), 'STORE': ('R', 'R'),
    'ADD':   ('R', 'R', 'R'), 'SUB': ('R', 'R', 'R'),
    'MUL':   ('R', 'R', 'R'), 'DIV': ('R', 'R', 'R'),
    'AND':   ('R', 'R', 'R'), 'OR':  ('R', 'R', 'R'),
    'NOT':   ('R', 'R'), 'CMP': ('R', 'R'),
    'JMP':   ('M',),     'JZ': ('M',),     'JN': ('M',),
    'JP':    ('M',),     'CALL': ('M',),   'RET': (),
    'PUSH':  ('R',),     'POP': ('R',),
    'IN':    ('R',),     'OUT': ('R',),
    'SHL':   ('R', 'R'), 'SHR': ('R', 'R'),
    'XOR':   ('R', 'R', 'R'),
    'ADDI':  ('R', 'R', 'I'), 'SUBI': ('R', 'R', 'I'),
}

# ─── Parser ──────────────────────────────────────────────────────────────────

def parse_value(s: str) -> int:
    """Parse a value: decimal, balanced ternary (with T prefix), or hex."""
    s = s.strip()
    if s.startswith('0t') or s.startswith('0T'):
        # Balanced ternary literal: 0t1T01
        mapping = {'T': -1, 't': -1, '0': 0, '1': 1}
        result = 0
        for ch in s[2:]:
            result = result * 3 + mapping[ch]
        return result
    elif s.startswith('0x') or s.startswith('0X'):
        return int(s, 16)
    elif s.startswith('0b') or s.startswith('0B'):
        return int(s, 2)
    else:
        return int(s)


def parse_register(s: str) -> int:
    """Parse a register name like R0-R26."""
    s = s.strip().upper()
    if s.startswith('R') and s[1:].isdigit():
        reg = int(s[1:])
        if 0 <= reg <= 26:
            return reg
    raise ValueError(f"Invalid register: {s}")


class Line:
    """Represents a parsed assembly line."""
    def __init__(self, line_num: int, raw: str):
        self.line_num = line_num
        self.raw = raw
        self.label: Optional[str] = None
        self.mnemonic: Optional[str] = None
        self.operands: list[str] = []
        self.directive: Optional[str] = None
        self.directive_args: list[str] = []
        self.is_comment = False
        self._parse()

    def _parse(self):
        text = self.raw.strip()
        # Remove comments: ; always starts a comment
        if ';' in text:
            text = text[:text.index(';')].strip()
        # # starts a comment only at beginning of line or after whitespace
        if text.startswith('#'):
            self.is_comment = True
            return
        if not text:
            self.is_comment = True
            return

        # Check for label
        if ':' in text and not text.startswith('.'):
            label_part, text = text.split(':', 1)
            self.label = label_part.strip()
            text = text.strip()
            if not text:
                return

        # Check for directive
        if text.startswith('.'):
            parts = text.split(None, 1)
            self.directive = parts[0].lower()
            if len(parts) > 1:
                self.directive_args = [a.strip() for a in parts[1].split(',')]
            return

        # Parse instruction
        parts = re.split(r'[\s,]+', text)
        self.mnemonic = parts[0].upper()
        self.operands = [p.strip() for p in parts[1:] if p.strip()]


# ─── Assembler ───────────────────────────────────────────────────────────────

class TriAsm:
    """Two-pass balanced ternary assembler."""

    def __init__(self):
        self.symbols: dict[str, int] = {}
        self.output: list[int] = []
        self.errors: list[str] = []
        self.origin: int = 0

    def assemble(self, source: str) -> list[int]:
        """Assemble source code. Returns list of integer opcodes."""
        self.symbols = {}
        self.output = []
        self.errors = []
        self.origin = 0

        lines = [Line(i + 1, line) for i, line in enumerate(source.splitlines())]

        # Pass 1: collect labels
        addr = self.origin
        for line in lines:
            if line.is_comment or line.directive == '.origin':
                if line.directive == '.origin':
                    self.origin = parse_value(line.directive_args[0])
                    addr = self.origin
                continue
            if line.label:
                self.symbols[line.label] = addr
            if line.mnemonic:
                addr += 1 + len(INSTR_FORMATS.get(line.mnemonic, ()))
            elif line.directive == '.word':
                addr += len(line.directive_args)
            elif line.directive == '.ascii':
                addr += len(line.directive_args[0].strip('"'))

        # Pass 2: generate code
        addr = self.origin
        for line in lines:
            if line.is_comment:
                continue

            if line.directive == '.origin':
                self.origin = parse_value(line.directive_args[0])
                addr = self.origin
                continue

            if line.directive == '.word':
                for arg in line.directive_args:
                    self.output.append(parse_value(arg))
                    addr += 1
                continue

            if line.directive == '.ascii':
                text = line.directive_args[0].strip('"')
                for ch in text:
                    self.output.append(ord(ch))
                    addr += 1
                continue

            if not line.mnemonic:
                continue

            if line.mnemonic not in OPCODES:
                self.errors.append(f"Line {line.line_num}: Unknown mnemonic '{line.mnemonic}'")
                continue

            fmt = INSTR_FORMATS.get(line.mnemonic, ())
            if len(line.operands) != len(fmt):
                self.errors.append(
                    f"Line {line.line_num}: {line.mnemonic} expects {len(fmt)} operands, "
                    f"got {len(line.operands)}"
                )
                continue

            self.output.append(OPCODES[line.mnemonic])
            addr += 1

            for operand, spec in zip(line.operands, fmt):
                if spec == 'R':
                    self.output.append(parse_register(operand))
                elif spec == 'M':
                    # Memory address: could be label or number
                    if operand in self.symbols:
                        self.output.append(self.symbols[operand])
                    else:
                        self.output.append(parse_value(operand))
                elif spec == 'I':
                    self.output.append(parse_value(operand))
                addr += 1

        return self.output

    def assemble_file(self, path: str) -> list[int]:
        with open(path) as f:
            return self.assemble(f.read())

    def to_binary_string(self) -> str:
        """Convert output to a ternary string representation."""
        lines = []
        for i, val in enumerate(self.output):
            trits = []
            n = val
            if n < 0:
                trits.append('T')
                n = -n
            if n == 0:
                trits = ['0']
            else:
                t = []
                while n > 0:
                    t.append(str(n % 3))
                    n //= 3
                trits.extend(reversed(t))
            lines.append(f"{i:>4}: {val:>6}  {''.join(trits)}")
        return '\n'.join(lines)


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Usage: tri_asm.py <source.asm> [--run]")
        print()
        print("Assembles a TriAsm source file and outputs the machine code.")
        print("With --run, executes the program on the TriCPU emulator.")
        sys.exit(1)

    source_path = sys.argv[1]
    should_run = '--run' in sys.argv

    with open(source_path) as f:
        source = f.read()

    asm = TriAsm()
    program = asm.assemble(source)

    if asm.errors:
        print("Assembly errors:")
        for err in asm.errors:
            print(f"  ❌ {err}")
        sys.exit(1)

    print(f"✅ Assembled {len(program)} words from {source_path}")
    print()
    print(asm.to_binary_string())

    if should_run:
        print()
        print("─" * 50)
        print("Running on TriCPU emulator...")
        print("─" * 50)
        sys.path.insert(0, str(Path(__file__).parent.parent / 'emulator'))
        from tri_cpu import TriCPU
        cpu = TriCPU()
        cpu.load_program(program)
        cpu.run()
        print(cpu.dump_state())
        if cpu.get_output():
            print(f"Output values: {cpu.get_output()}")


if __name__ == '__main__':
    main()
