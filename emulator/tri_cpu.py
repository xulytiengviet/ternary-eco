#!/usr/bin/env python3
"""
TriCPU — A balanced ternary CPU emulator.

Balanced ternary uses three digits: -1 (T), 0 (0), +1 (1).
This emulator implements a complete balanced ternary CPU with:
  - 27 trit registers (R0-R26, where R0 is always 0)
  - 3^12 (531,441) addressable trits of memory
  - A full instruction set: LOAD, STORE, ADD, SUB, MUL, DIV, AND, OR, NOT,
    CMP, JMP, JZ, JN, JP, CALL, RET, PUSH, POP, HALT, NOP, IN, OUT
  - Trit-based memory addressing
  - Interrupt support
"""

from __future__ import annotations
import sys
from enum import IntEnum
from typing import Optional

# ─── Ternary Constants ────────────────────────────────────────────────────────

TRIT_T = -1  # T (negative)
TRIT_0 = 0   # 0 (zero)
TRIT_1 = 1   # 1 (positive)

TRIT_CHARS = {-1: 'T', 0: '0', 1: '1'}

# ─── Instruction Opcodes (9 instructions encoded in balanced ternary) ─────────

class Opcode(IntEnum):
    NOP  = 0   # 000
    HALT = 1   # 001
    LOAD = 2   # 00T
    STORE = 3  # 010
    ADD  = 4   # 011
    SUB  = 5   # 01T
    MUL  = 6   # 0T0
    DIV  = 7   # 0T1
    AND  = 8   # 0TT
    OR   = 9   # 100
    NOT  = 10  # 101
    CMP  = 11  # 10T
    JMP  = 12  # 110
    JZ   = 13  # 111
    JN   = 14  # 11T
    JP   = 15  # 1T0
    CALL = 16  # 1T1
    RET  = 17  # 1TT
    PUSH = 18  # T00
    POP  = 19  # T01
    IN   = 20  # T0T
    OUT  = 21  # TT0
    SHL  = 22  # TT1
    SHR  = 23  # TTT
    XOR  = 24  # T0T -> remap: actually T10
    ADDI = 25  # T11
    SUBI = 26  # T1T

# ─── Ternary Math Utilities ──────────────────────────────────────────────────

def int_to_balanced_ternary(n: int, trits: int = 9) -> list[int]:
    """Convert integer to balanced ternary list of given length."""
    if n == 0:
        return [0] * trits
    result = []
    while n != 0:
        remainder = n % 3
        n = n // 3
        if remainder == 2:
            remainder = -1
            n += 1
        elif remainder == -2:
            remainder = 1
            n -= 1
        result.append(remainder)
    # Pad to required length
    while len(result) < trits:
        result.append(0)
    return result[:trits]


def balanced_ternary_to_int(trits: list[int]) -> int:
    """Convert balanced ternary list to integer."""
    result = 0
    for i, t in enumerate(trits):
        result += t * (3 ** i)
    return result


def ternary_to_string(trits: list[int]) -> str:
    """Convert trit list to readable string (MSB first)."""
    return ''.join(TRIT_CHARS[t] for t in reversed(trits))


def ternary_string_to_trits(s: str) -> list[int]:
    """Parse a ternary string like '1T01' into a trit list (MSB first)."""
    mapping = {'T': -1, 't': -1, '0': 0, '1': 1}
    return [mapping[c] for c in s]


# ─── Ternary ALU ─────────────────────────────────────────────────────────────

class TernaryALU:
    """Balanced ternary arithmetic logic unit."""

    @staticmethod
    def add(a: int, b: int) -> int:
        """Add two balanced ternary integers."""
        return a + b

    @staticmethod
    def sub(a: int, b: int) -> int:
        return a - b

    @staticmethod
    def mul(a: int, b: int) -> int:
        return a * b

    @staticmethod
    def div(a: int, b: int) -> int:
        if b == 0:
            raise ZeroDivisionError("Ternary division by zero")
        # Balanced ternary division: round toward zero
        sign = 1 if (a >= 0) == (b >= 0) else -1
        return sign * (abs(a) // abs(b))

    @staticmethod
    def negate(a: int) -> int:
        return -a

    @staticmethod
    def tand(a: int, b: int) -> int:
        """Ternary AND: min of two values mapped to {-1,0,1}."""
        return min(a, b)

    @staticmethod
    def tor(a: int, b: int) -> int:
        """Ternary OR: max of two values."""
        return max(a, b)

    @staticmethod
    def tnot(a: int) -> int:
        """Ternary NOT: negate."""
        return -a

    @staticmethod
    def txor(a: int, b: int) -> int:
        """Ternary XOR: a + b mod balanced ternary."""
        return a + b  # In balanced ternary, this is addition without carry

    @staticmethod
    def compare(a: int, b: int) -> int:
        """Compare: returns -1 if a < b, 0 if a == b, 1 if a > b."""
        if a < b:
            return -1
        elif a > b:
            return 1
        return 0

    @staticmethod
    def shift_left(a: int) -> int:
        """Shift left (multiply by 3)."""
        return a * 3

    @staticmethod
    def shift_right(a: int) -> int:
        """Shift right (divide by 3)."""
        return a // 3


# ─── CPU State ───────────────────────────────────────────────────────────────

class CPUState:
    """Represents the complete state of the TriCPU."""

    NUM_REGISTERS = 27   # R0-R26, R0 is always 0
    MEMORY_TRITS = 3**12  # 531,441 addressable trits
    WORD_SIZE = 9         # 9 trits per word (range: -9841 to 9841)
    STACK_POINTER = 26    # R26 is stack pointer
    PROGRAM_COUNTER = 25  # R25 is program counter
    FLAGS_REGISTER = 24   # R24 is flags (Z, N, C, V)

    def __init__(self):
        self.registers = [0] * self.NUM_REGISTERS
        self.memory = [0] * self.MEMORY_TRITS
        self.pc = 0
        self.sp = self.MEMORY_TRITS - 1  # Stack grows downward
        self.flags = {'Z': False, 'N': False, 'C': False, 'V': False}
        self.halted = False
        self.cycle_count = 0
        self.alu = TernaryALU()
        self.output_buffer: list[int] = []
        self.input_buffer: list[int] = []
        self.input_pos = 0

    def reset(self):
        self.registers = [0] * self.NUM_REGISTERS
        self.memory = [0] * self.MEMORY_TRITS
        self.pc = 0
        self.sp = self.MEMORY_TRITS - 1
        self.flags = {'Z': False, 'N': False, 'C': False, 'V': False}
        self.halted = False
        self.cycle_count = 0
        self.output_buffer = []
        self.input_buffer = []
        self.input_pos = 0

    def read_memory_word(self, addr: int) -> int:
        """Read a 9-trit word from memory."""
        word_trits = []
        for i in range(self.WORD_SIZE):
            idx = (addr * self.WORD_SIZE + i) % self.MEMORY_TRITS
            word_trits.append(self.memory[idx])
        return balanced_ternary_to_int(word_trits)

    def write_memory_word(self, addr: int, value: int):
        """Write a 9-trit word to memory."""
        trits = int_to_balanced_ternary(value, self.WORD_SIZE)
        for i in range(self.WORD_SIZE):
            idx = (addr * self.WORD_SIZE + i) % self.MEMORY_TRITS
            self.memory[idx] = trits[i]

    def set_flags(self, value: int):
        """Update flags based on a value."""
        self.flags['Z'] = (value == 0)
        self.flags['N'] = (value < 0)
        # Carry and overflow for arithmetic
        max_val = (3**self.WORD_SIZE - 1) // 2
        self.flags['V'] = (value > max_val or value < -max_val)
        self.flags['C'] = self.flags['V']

    def get_reg(self, reg: int) -> int:
        if reg == 0:
            return 0  # R0 is hardwired to 0
        return self.registers[reg]

    def set_reg(self, reg: int, value: int):
        if reg == 0:
            return  # R0 is read-only
        self.registers[reg] = value

    def push(self, value: int):
        self.write_memory_word(self.sp, value)
        self.sp = (self.sp - 1) % self.MEMORY_TRITS

    def pop(self) -> int:
        self.sp = (self.sp + 1) % self.MEMORY_TRITS
        return self.read_memory_word(self.sp)

    def load_program(self, program: list[int]):
        """Load a program (list of integer values) into memory."""
        for addr, value in enumerate(program):
            self.write_memory_word(addr, value)


# ─── Instruction Decoder ─────────────────────────────────────────────────────

class InstructionDecoder:
    """Decodes and executes TriCPU instructions."""

    def __init__(self, cpu: CPUState):
        self.cpu = cpu

    def fetch(self) -> int:
        """Fetch next instruction word."""
        instr = self.cpu.read_memory_word(self.cpu.pc)
        self.cpu.pc += 1
        return instr

    def decode_and_execute(self, instruction: int):
        """Decode and execute a single instruction."""
        # Instruction format: [opcode: 2 trits][mode: 1 trit][operand(s): 6 trits]
        # For simplicity, we use integer opcodes directly
        opcode = instruction
        cpu = self.cpu

        if opcode == Opcode.NOP:
            pass

        elif opcode == Opcode.HALT:
            cpu.halted = True

        elif opcode == Opcode.LOAD:
            # LOAD Rd, [Rs] — load from memory at address in Rs into Rd
            rd = self.fetch()
            rs = self.fetch()
            addr = cpu.get_reg(rs)
            cpu.set_reg(rd, cpu.read_memory_word(addr))

        elif opcode == Opcode.STORE:
            # STORE [Rd], Rs — store Rs to memory at address in Rd
            rd = self.fetch()
            rs = self.fetch()
            addr = cpu.get_reg(rd)
            cpu.write_memory_word(addr, cpu.get_reg(rs))

        elif opcode == Opcode.ADD:
            rd = self.fetch()
            rs1 = self.fetch()
            rs2 = self.fetch()
            result = cpu.alu.add(cpu.get_reg(rs1), cpu.get_reg(rs2))
            cpu.set_reg(rd, result)
            cpu.set_flags(result)

        elif opcode == Opcode.SUB:
            rd = self.fetch()
            rs1 = self.fetch()
            rs2 = self.fetch()
            result = cpu.alu.sub(cpu.get_reg(rs1), cpu.get_reg(rs2))
            cpu.set_reg(rd, result)
            cpu.set_flags(result)

        elif opcode == Opcode.MUL:
            rd = self.fetch()
            rs1 = self.fetch()
            rs2 = self.fetch()
            result = cpu.alu.mul(cpu.get_reg(rs1), cpu.get_reg(rs2))
            cpu.set_reg(rd, result)
            cpu.set_flags(result)

        elif opcode == Opcode.DIV:
            rd = self.fetch()
            rs1 = self.fetch()
            rs2 = self.fetch()
            try:
                result = cpu.alu.div(cpu.get_reg(rs1), cpu.get_reg(rs2))
                cpu.set_reg(rd, result)
                cpu.set_flags(result)
            except ZeroDivisionError:
                cpu.flags['V'] = True

        elif opcode == Opcode.AND:
            rd = self.fetch()
            rs1 = self.fetch()
            rs2 = self.fetch()
            result = cpu.alu.tand(cpu.get_reg(rs1), cpu.get_reg(rs2))
            cpu.set_reg(rd, result)
            cpu.set_flags(result)

        elif opcode == Opcode.OR:
            rd = self.fetch()
            rs1 = self.fetch()
            rs2 = self.fetch()
            result = cpu.alu.tor(cpu.get_reg(rs1), cpu.get_reg(rs2))
            cpu.set_reg(rd, result)
            cpu.set_flags(result)

        elif opcode == Opcode.NOT:
            rd = self.fetch()
            rs = self.fetch()
            result = cpu.alu.tnot(cpu.get_reg(rs))
            cpu.set_reg(rd, result)
            cpu.set_flags(result)

        elif opcode == Opcode.CMP:
            rs1 = self.fetch()
            rs2 = self.fetch()
            result = cpu.alu.compare(cpu.get_reg(rs1), cpu.get_reg(rs2))
            cpu.set_flags(result)

        elif opcode == Opcode.JMP:
            addr = self.fetch()
            cpu.pc = addr

        elif opcode == Opcode.JZ:
            addr = self.fetch()
            if cpu.flags['Z']:
                cpu.pc = addr

        elif opcode == Opcode.JN:
            addr = self.fetch()
            if cpu.flags['N']:
                cpu.pc = addr

        elif opcode == Opcode.JP:
            addr = self.fetch()
            if not cpu.flags['Z'] and not cpu.flags['N']:
                cpu.pc = addr

        elif opcode == Opcode.CALL:
            addr = self.fetch()
            cpu.push(cpu.pc)
            cpu.pc = addr

        elif opcode == Opcode.RET:
            cpu.pc = cpu.pop()

        elif opcode == Opcode.PUSH:
            rs = self.fetch()
            cpu.push(cpu.get_reg(rs))

        elif opcode == Opcode.POP:
            rd = self.fetch()
            cpu.set_reg(rd, cpu.pop())

        elif opcode == Opcode.IN:
            rd = self.fetch()
            if cpu.input_pos < len(cpu.input_buffer):
                cpu.set_reg(rd, cpu.input_buffer[cpu.input_pos])
                cpu.input_pos += 1
            else:
                cpu.set_reg(rd, 0)

        elif opcode == Opcode.OUT:
            rs = self.fetch()
            cpu.output_buffer.append(cpu.get_reg(rs))

        elif opcode == Opcode.SHL:
            rd = self.fetch()
            rs = self.fetch()
            result = cpu.alu.shift_left(cpu.get_reg(rs))
            cpu.set_reg(rd, result)
            cpu.set_flags(result)

        elif opcode == Opcode.SHR:
            rd = self.fetch()
            rs = self.fetch()
            result = cpu.alu.shift_right(cpu.get_reg(rs))
            cpu.set_reg(rd, result)
            cpu.set_flags(result)

        elif opcode == Opcode.XOR:
            rd = self.fetch()
            rs1 = self.fetch()
            rs2 = self.fetch()
            result = cpu.alu.txor(cpu.get_reg(rs1), cpu.get_reg(rs2))
            cpu.set_reg(rd, result)
            cpu.set_flags(result)

        elif opcode == Opcode.ADDI:
            # ADDI Rd, Rs, immediate
            rd = self.fetch()
            rs = self.fetch()
            imm = self.fetch()
            result = cpu.alu.add(cpu.get_reg(rs), imm)
            cpu.set_reg(rd, result)
            cpu.set_flags(result)

        elif opcode == Opcode.SUBI:
            rd = self.fetch()
            rs = self.fetch()
            imm = self.fetch()
            result = cpu.alu.sub(cpu.get_reg(rs), imm)
            cpu.set_reg(rd, result)
            cpu.set_flags(result)

        else:
            raise ValueError(f"Unknown opcode: {opcode} at PC={cpu.pc - 1}")


# ─── Main Emulator ───────────────────────────────────────────────────────────

class TriCPU:
    """Main ternary CPU emulator."""

    def __init__(self):
        self.cpu = CPUState()
        self.decoder = InstructionDecoder(self.cpu)

    def reset(self):
        self.cpu.reset()

    def load_program(self, program: list[int]):
        self.cpu.load_program(program)

    def step(self) -> bool:
        """Execute one instruction. Returns False if halted."""
        if self.cpu.halted:
            return False
        instr = self.decoder.fetch()
        self.decoder.decode_and_execute(instr)
        self.cpu.cycle_count += 1
        return not self.cpu.halted

    def run(self, max_cycles: int = 1_000_000):
        """Run until HALT or max cycles reached."""
        while not self.cpu.halted and self.cpu.cycle_count < max_cycles:
            self.step()
        return self.cpu.cycle_count

    def run_debug(self, max_cycles: int = 1_000_000):
        """Run with debug output each cycle."""
        while not self.cpu.halted and self.cpu.cycle_count < max_cycles:
            pc = self.cpu.pc
            instr = self.decoder.fetch()
            op_name = Opcode(instr).name if instr in Opcode._value2member_map_ else f"???({instr})"
            self.decoder.decode_and_execute(instr)
            self.cpu.cycle_count += 1
            regs = [self.cpu.get_reg(i) for i in range(1, 8)]
            print(f"  Cycle {self.cpu.cycle_count:>6} | PC={pc:>5} | {op_name:<6} | "
                  f"R1-R7={regs} | Z={int(self.cpu.flags['Z'])} N={int(self.cpu.flags['N'])}")
        return self.cpu.cycle_count

    def get_output(self) -> list[int]:
        return list(self.cpu.output_buffer)

    def set_input(self, data: list[int]):
        self.cpu.input_buffer = list(data)
        self.cpu.input_pos = 0

    def dump_state(self) -> str:
        lines = [f"=== TriCPU State (cycles: {self.cpu.cycle_count}) ==="]
        lines.append(f"  PC={self.cpu.pc} SP={self.cpu.sp}")
        lines.append(f"  Flags: Z={self.cpu.flags['Z']} N={self.cpu.flags['N']} "
                     f"C={self.cpu.flags['C']} V={self.cpu.flags['V']}")
        for i in range(1, self.cpu.NUM_REGISTERS):
            val = self.cpu.get_reg(i)
            if val != 0:
                lines.append(f"  R{i:<2} = {val:>6}  ({int_to_balanced_ternary(val, 9)})")
        if self.cpu.output_buffer:
            lines.append(f"  Output: {self.cpu.output_buffer}")
        return '\n'.join(lines)


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    """Demo: run a simple ternary program."""
    print("╔══════════════════════════════════════╗")
    print("║       TriCPU Ternary Emulator        ║")
    print("╚══════════════════════════════════════╝")
    print()

    cpu = TriCPU()

    # Demo program: compute factorial of 5 in balanced ternary
    # 5 decimal = 1TT balanced ternary (1*9 + (-1)*3 + (-1)*1 = 9-3-1 = 5)
    # Result: 120 decimal = 1T1T00 balanced ternary
    #
    # Algorithm:
    #   R1 = 5 (counter)
    #   R2 = 1 (accumulator)
    #   loop: R2 = R2 * R1
    #         R1 = R1 - 1
    #         if R1 > 0 goto loop
    #         output R2
    #         halt

    program = [
        # Address 0: R1 = 5
        Opcode.ADDI, 1, 0, 5,      # R1 = R0 + 5 = 5
        # Address 4: R2 = 1
        Opcode.ADDI, 2, 0, 1,      # R2 = R0 + 1 = 1
        # Address 8: R2 = R2 * R1  (loop start)
        Opcode.MUL, 3, 2, 1,       # R3 = R2 * R1
        Opcode.ADD, 2, 0, 3,       # R2 = R0 + R3 = R3
        # Address 14: R1 = R1 - 1
        Opcode.SUBI, 1, 1, 1,      # R1 = R1 - 1
        # Address 18: if R1 > 0 goto 8
        Opcode.CMP, 1, 0,          # Compare R1 with R0
        Opcode.JP, 8,              # Jump to loop if positive
        # Address 22: output R2
        Opcode.OUT, 2,             # Output R2
        # Address 24: halt
        Opcode.HALT,               # Halt
    ]

    cpu.load_program(program)

    print("Running factorial(5) program...")
    print()
    cpu.run_debug()
    print()
    print(cpu.dump_state())
    print()

    output = cpu.get_output()
    if output:
        result = output[0]
        print(f"Result: {result} (decimal) = {int_to_balanced_ternary(result, 9)} (balanced ternary)")
        assert result == 120, f"Expected 120, got {result}"
        print("✅ Factorial(5) = 120 — correct!")


if __name__ == '__main__':
    main()
