# 🔺 Ternary Computing Ecosystem

## 🇻🇳 Ternary Eco Lab — CVNSS4.0 × BilaTiny × TinyLLM × Edge AI

**Phòng thí nghiệm tương tác mới:** [docs/index.html](docs/index.html) · [Hướng dẫn tái lập](docs/REPRODUCIBILITY.md) · [Kiểm thử Node](tests/lab.test.cjs)

Trang web bổ sung cho hệ thống Python bên dưới, không thay thế mã gốc. Mở trong trình duyệt để chạy:

- **Vietnamese → CVNSS4.0 v5 audit-safe → Base27 → 3 trit/ký hiệu**, cùng candidate graph và chính sách giải mã canonical (56 nhóm nhập nhằng).
- **Pack5:** 5 balanced trits/byte, giải nén lossless với metadata độ dài; đối chiếu biểu diễn 2-bit/trit.
- **BilaTiny:** typed compiler subset gồm trit, tadd, tmul, emit; sinh pseudo-bytecode 4 byte/lệnh và chạy VM JavaScript 8 thanh ghi.
- **TinyLLM weights:** phép thử lượng tử hóa ma trận giả lập, so sánh FP32/sparse trit và MSE có seed cố định.
- **Targets:** ví dụ C cho ESP32-S3, ví dụ VHDL-2008 cho FPGA/NHDL và manifest xuất cục bộ; chưa có firmware/bitstream hoặc checkpoint AI đã huấn luyện.

**Lưu ý khoa học:** Trạng thái trit ở đây được mô phỏng trên chip nhị phân; không suy diễn thành ISA tam phân vật lý. CVNSS4.0 là mã nhiều-một, vì vậy văn bản gốc không luôn tự động khôi phục 100% khi thiếu ngữ cảnh. Kết quả CI chỉ xác nhận thuật toán tham chiếu.

### Quickstart

    python -m http.server 8000

Truy cập http://localhost:8000/docs/ và chạy `node --test tests/lab.test.cjs` để kiểm tra. Có thể triển khai GitHub Pages từ branch `main`, thư mục `/docs` trong Settings → Pages.

**Nguồn tham khảo mở:** [Ternary Inference Sim](https://github.com/SuperInstance/ternary-inference-sim) · [TIS](https://github.com/rfi-irfos/ternary-intelligence-stack) · [Rusty Penguin](https://github.com/rfi-irfos/rusty-penguin) · [Trilang](https://github.com/trilang/trilang) · [ternary-ecosystem (upstream)](https://github.com/theeteeshrimp/ternary-ecosystem). Các repo bên ngoài được liên kết, không sao chép mã có giấy phép không tương thích.

---


> A complete balanced ternary computing stack — from CPU emulator to operating system.

**Balanced ternary** is a non-standard numeral system that uses three digits: **-1 (T)**, **0**, and **+1**. Unlike binary (base-2), balanced ternary is naturally signed, has symmetric rounding, and can represent numbers more compactly. This project implements a full software ecosystem for a balanced ternary computer.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│              User Programs (.tri)                │
├─────────────────────────────────────────────────┤
│           TriLang Compiler (trilang.py)          │
│    Source → Lexer → Parser → AST → Assembly     │
├─────────────────────────────────────────────────┤
│          TriAsm Assembler (tri_asm.py)           │
│    Assembly → Two-pass → Machine Code            │
├─────────────────────────────────────────────────┤
│          TriOS Operating System (trios.py)       │
│  Processes │ Memory │ Filesystem │ Syscalls     │
├─────────────────────────────────────────────────┤
│         TriCPU Emulator (tri_cpu.py)             │
│  27 Registers │ ALU │ Decoder │ 27 Opcodes     │
├─────────────────────────────────────────────────┤
│         TriLib Standard Library (tri_stdlib.py)  │
│  Math │ Sorting │ Data Structures │ Conversions │
└─────────────────────────────────────────────────┘
```

## 📁 Repository Structure

```
ternary-ecosystem/
├── README.md                  # This file
├── LICENSE                    # MIT License
├── emulator/
│   └── tri_cpu.py             # Balanced ternary CPU emulator
├── assembler/
│   └── tri_asm.py             # Two-pass ternary assembler
├── compiler/
│   └── trilang.py             # TriLang high-level language compiler
├── os/
│   └── trios.py               # TriOS operating system kernel
├── stdlib/
│   └── tri_stdlib.py          # Standard library
├── examples/
│   ├── factorial.asm          # Factorial in assembly
│   ├── fibonacci.asm          # Fibonacci in assembly
│   ├── hello.tri              # Hello World in TriLang
│   └── sorting.tri            # Sorting demo in TriLang
└── docs/
    └── architecture.md        # Detailed architecture docs
```

## 🚀 Quick Start

### Requirements
- Python 3.10+

### Run the CPU Emulator

```bash
cd emulator
python tri_cpu.py
```

This runs a demo program that computes 5! (factorial) on the ternary CPU.

### Assemble a Program

```bash
cd assembler
python tri_asm.py ../examples/factorial.asm --run
```

### Compile TriLang

```bash
cd compiler
python trilang.py ../examples/hello.tri --asm --run
```

### Run the OS

```bash
cd os
python trios.py
```

### Run the Standard Library

```bash
cd stdlib
python tri_stdlib.py
```

## 🔢 Balanced Ternary Basics

| Decimal | Balanced Ternary | Calculation |
|---------|-----------------|-------------|
| -5      | TT              | -3 + -1 = -5 |
| -4      | T1              | -3 + 1 = -4 |
| -3      | T0              | -3 + 0 = -3 |
| -2      | T1              | -3 + 1 = -2 |
| -1      | T               | -1 |
| 0       | 0               | 0 |
| 1       | 1               | 1 |
| 2       | 1T              | 3 + -1 = 2 |
| 3       | 10              | 3 + 0 = 3 |
| 4       | 11              | 3 + 1 = 4 |
| 5       | 1TT             | 9 + -3 + -1 = 5 |
| 42      | 1T1T0           | 27-9+3-1 = 42 |

**Key properties:**
- No separate sign bit needed — the leading trit indicates sign
- Rounding = truncation (simpler hardware)
- Addition/subtraction are naturally signed
- More information-dense than binary (log₂(3) ≈ 1.585 bits per trit)

## 🖥️ TriCPU Instruction Set

| Opcode | Operands | Description |
|--------|----------|-------------|
| `NOP`  | — | No operation |
| `HALT` | — | Stop execution |
| `LOAD` | Rd, Rs | Load from memory[Rs] into Rd |
| `STORE`| Rd, Rs | Store Rs to memory[Rd] |
| `ADD`  | Rd, Rs1, Rs2 | Rd = Rs1 + Rs2 |
| `SUB`  | Rd, Rs1, Rs2 | Rd = Rs1 - Rs2 |
| `MUL`  | Rd, Rs1, Rs2 | Rd = Rs1 × Rs2 |
| `DIV`  | Rd, Rs1, Rs2 | Rd = Rs1 ÷ Rs2 |
| `AND`  | Rd, Rs1, Rs2 | Rd = min(Rs1, Rs2) |
| `OR`   | Rd, Rs1, Rs2 | Rd = max(Rs1, Rs2) |
| `NOT`  | Rd, Rs | Rd = -Rs |
| `CMP`  | Rs1, Rs2 | Set flags from Rs1 - Rs2 |
| `JMP`  | addr | Unconditional jump |
| `JZ`   | addr | Jump if zero |
| `JN`   | addr | Jump if negative |
| `JP`   | addr | Jump if positive |
| `CALL` | addr | Call subroutine |
| `RET`  | — | Return from subroutine |
| `PUSH` | Rs | Push to stack |
| `POP`  | Rd | Pop from stack |
| `IN`   | Rd | Read input |
| `OUT`  | Rs | Write output |
| `SHL`  | Rd, Rs | Shift left (×3) |
| `SHR`  | Rd, Rs | Shift right (÷3) |
| `XOR`  | Rd, Rs1, Rs2 | Ternary XOR |
| `ADDI` | Rd, Rs, imm | Rd = Rs + immediate |
| `SUBI` | Rd, Rs, imm | Rd = Rs - immediate |

## 📝 TriLang Language Reference

### Variables
```trilang
var x = 42;
var name = 0t1T01;   # Balanced ternary literal
```

### Arithmetic
```trilang
var sum = a + b;
var diff = a - b;
var prod = a * b;
var quot = a / b;
var rem = a % b;
```

### Control Flow
```trilang
if (x > 0) {
    print(x);
} else {
    print(0);
}

while (i < 10) {
    i = i + 1;
}

for (var i = 0; i < 10; i = i + 1) {
    print(i);
}
```

### Functions
```trilang
func add(a, b) {
    return a + b;
}

func main() {
    var result = add(3, 4);
    print(result);
}
```

### Built-in Functions
- `print(value)` — Output a value
- `input()` — Read a value

## 🏛️ TriOS Operating System

### Features
- **Process Management**: Create, schedule, and terminate processes
- **Ternary Priority Scheduling**: Three priority levels (-1, 0, 1) with round-robin within each level
- **Memory Management**: First-fit allocation with bitmap tracking
- **TriFS File System**: Hierarchical file system with balanced ternary addressing
- **27 System Calls**: Process, memory, file, and I/O operations
- **Interactive Shell**: Command-line interface

### System Calls
| # | Call | Description |
|---|------|-------------|
| 0 | EXIT | Terminate process |
| 1 | FORK | Create child process |
| 2 | READ | Read from file |
| 3 | WRITE | Write to file |
| 4 | OPEN | Open file |
| 5 | CLOSE | Close file |
| 6 | WAIT | Wait for child |
| 7 | EXEC | Execute program |
| 8 | GETPID | Get process ID |
| 9 | GETPPID | Get parent PID |
| 10 | YIELD | Yield CPU |
| 11 | SLEEP | Sleep for N cycles |
| 12 | MALLOC | Allocate memory |
| 13 | FREE | Free memory |
| 14 | PRINT | Print to console |
| 15 | INPUT | Read from console |
| 16 | TIME | Get system time |
| 17-26 | Various | File and signal operations |

### Shell Commands
```
help, ps, mem, ls, cat, touch, mkdir, rm, tree, run, status, clear, reboot, shutdown
```

## 📚 TriLib Standard Library

- **Math**: GCD, LCM, power, factorial, Fibonacci, primality testing
- **Conversions**: Decimal ↔ balanced ternary
- **Sorting**: Ternary-adapted merge sort
- **Data Structures**: Stack, circular queue, linked list

## 🧪 Running Tests

```bash
# Test the emulator
python emulator/tri_cpu.py

# Test the assembler
python assembler/tri_asm.py examples/factorial.asm --run

# Test the compiler
python compiler/trilang.py examples/hello.tri --asm --run

# Test the OS
python os/trios.py

# Test the stdlib
python stdlib/tri_stdlib.py
```

## 📖 Further Reading

- [Donald Knuth](https://www-cs-faculty.stanford.edu/~knuth/) — "The Art of Computer Programming, Vol. 2" (balanced ternary)
- [Ternary Computer](https://en.wikipedia.org/wiki/Ternary_computer) — Wikipedia
- [Balanced Ternary](https://en.wikipedia.org/wiki/Balanced_ternary) — Wikipedia
- [Setun](https://en.wikipedia.org/wiki/Setun) — The Soviet ternary computer (1958)

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

## 🤝 Contributing

This is a demonstration project. Feel free to fork, experiment, and extend! Ideas:
- Add more TriLang features (strings, arrays, structs)
- Implement a ternary display driver
- Add networking syscalls
- Build a ternary floating-point unit
- Create a web-based IDE for TriLang

---

*Built with 🔺 by Shrimp Code — exploring the future that binary almost wasn't.*
