# TriCPU Architecture Reference

## Design Philosophy

The TriCPU is a balanced ternary processor designed for elegance and simplicity. Key design decisions:

1. **Balanced ternary throughout** — All data paths, addresses, and operations use balanced ternary
2. **27 registers** — Chosen because 27 = 3³, a natural ternary unit
3. **9-trit words** — Each word holds values from -9841 to +9841
4. **27 opcodes** — One per ternary "digit pair" in a 2-trit encoding

## Memory Model

```
Total addressable trits: 3^12 = 531,441
Word size: 9 trits
Total words: 3^12 / 9 = 59,049
Address range: 0 to 59,048 (decimal)
                 0 to 100000000 (balanced ternary)
```

### Memory Map
```
0x00000 - 0x0FFFF  : Kernel / OS reserved
0x10000 - 0x7FFFF  : User programs
0x80000 - 0xEFFFF  : Data / heap
0xF0000 - 0xFFFFF  : Stack (grows downward)
```

## Register Layout

| Register | Purpose |
|----------|---------|
| R0       | Hardwired to zero (read-only) |
| R1-R7    | General purpose (caller-saved) |
| R8-R15   | General purpose (callee-saved) |
| R16-R23  | General purpose |
| R24      | Flags register (Z, N, C, V) |
| R25      | Program counter (PC) |
| R26      | Stack pointer (SP) |

## Instruction Encoding

Each instruction is encoded as a single 9-trit word:

```
[Opcode: 2 trits] [Mode: 1 trit] [Operand 1: 2 trits] [Operand 2: 2 trits] [Operand 3: 2 trits]
```

For instructions with fewer operands, unused fields are zero-padded.

## ALU Operations

The Ternary ALU supports:

| Operation | Ternary Definition |
|-----------|-------------------|
| ADD | Standard integer addition |
| SUB | Standard integer subtraction |
| MUL | Standard integer multiplication |
| DIV | Integer division (round toward zero) |
| AND | min(a, b) |
| OR | max(a, b) |
| NOT | -a |
| XOR | a + b (mod 3, per trit) |
| SHL | a × 3 |
| SHR | a ÷ 3 |

## Interrupt Vector Table

| Address | Interrupt |
|---------|-----------|
| 0 | Reset |
| 1 | Illegal instruction |
| 2 | Division by zero |
| 3 | System call |
| 4 | Timer |
| 5 | I/O ready |

## Pipeline (Conceptual)

```
Fetch → Decode → Execute → Memory → Writeback
  1       2        3         4        5      (cycles)
```

The emulator runs a single-cycle model for simplicity, but the ISA is designed to support pipelining.

## Comparison with Binary

| Feature | Binary | Balanced Ternary |
|---------|--------|-----------------|
| Digits | 0, 1 | T(-1), 0, 1(1) |
| Sign | Separate sign bit | Leading trit |
| Rounding | Complex | Truncation |
| Digits for 100 | 7 bits | 5 trits |
| Digits for 1000 | 10 bits | 7 trits |
| Information density | 1 bit/trit | ~1.585 bits/trit |
