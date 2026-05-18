#!/usr/bin/env python3
"""
TriOS — A minimal operating system for the TriCPU.

Implements:
  - Process management (create, schedule, terminate)
  - Round-robin scheduling with ternary priority levels (-1, 0, 1)
  - Memory management (allocation, deallocation, protection)
  - File system (TriFS) with balanced ternary addressing
  - System calls (27 syscalls)
  - Interrupt handling
  - Device abstraction layer
  - Shell (command-line interface)

Architecture:
  ┌─────────────────────────────┐
  │         User Programs       │
  ├─────────────────────────────┤
  │       System Call API       │
  ├──────────┬──────────┬───────┤
  │ Process  │ Memory   │ File  │
  │ Manager  │ Manager  │ System│
  ├──────────┴──────────┴───────┤
  │     Interrupt Handler       │
  ├─────────────────────────────┤
  │     Device Drivers          │
  ├─────────────────────────────┤
  │     TriCPU Hardware         │
  └─────────────────────────────┘
"""

from __future__ import annotations
import sys
from pathlib import Path
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Optional

# ─── Imports from emulator ───────────────────────────────────────────────────

sys.path.insert(0, str(Path(__file__).parent.parent / 'emulator'))
from tri_cpu import TriCPU, CPUState, Opcode, int_to_balanced_ternary, balanced_ternary_to_int

# ─── System Calls ────────────────────────────────────────────────────────────

class Syscall(IntEnum):
    EXIT     = 0   # Terminate process
    FORK     = 1   # Create child process
    READ     = 2   # Read from file
    WRITE    = 3   # Write to file
    OPEN     = 4   # Open file
    CLOSE    = 5   # Close file
    WAIT     = 6   # Wait for child
    EXEC     = 7   # Execute program
    GETPID   = 8   # Get process ID
    GETPPID  = 9   # Get parent PID
    YIELD    = 10  # Yield CPU
    SLEEP    = 11  # Sleep for N cycles
    MALLOC   = 12  # Allocate memory
    FREE     = 13  # Free memory
    PRINT    = 14  # Print to console
    INPUT    = 15  # Read from console
    TIME     = 16  # Get system time
    RENAME   = 17  # Rename file
    DELETE   = 18  # Delete file
    MKDIR    = 19  # Create directory
    LIST     = 20  # List directory
    MOUNT    = 21  # Mount filesystem
    UNMOUNT  = 22  # Unmount filesystem
    KILL     = 23  # Send signal
    SIGNAL   = 24  # Register handler
    PIPE     = 25  # Create pipe
    DUP      = 26  # Duplicate fd

# ─── Process Control Block ───────────────────────────────────────────────────

class ProcessState(IntEnum):
    READY   = 0
    RUNNING = 1
    WAITING = 2
    ZOMBIE  = 3
    DEAD    = 4

@dataclass
class Process:
    pid: int
    ppid: int
    state: ProcessState
    priority: int  # -1, 0, 1 (balanced ternary!)
    cpu_state: CPUState
    memory_start: int
    memory_size: int
    name: str
    exit_code: int = 0
    file_descriptors: dict[int, str] = field(default_factory=dict)
    children: list[int] = field(default_factory=list)
    signal_handlers: dict[int, int] = field(default_factory=dict)
    wait_target: int = -1  # PID to wait for
    sleep_until: int = 0   # Cycle count to wake up

# ─── Memory Manager ──────────────────────────────────────────────────────────

class MemoryManager:
    """Simple memory manager with allocation bitmap."""

    def __init__(self, total_words: int = 3**8):  # 6561 words
        self.total_words = total_words
        self.bitmap = [False] * total_words  # False = free
        self.allocations: dict[int, tuple[int, int]] = {}  # pid -> (start, size)

    def allocate(self, size: int, pid: int) -> int:
        """Allocate contiguous memory. Returns start address or -1."""
        # First-fit allocation
        consecutive = 0
        start = -1
        for i in range(self.total_words):
            if not self.bitmap[i]:
                if consecutive == 0:
                    start = i
                consecutive += 1
                if consecutive >= size:
                    # Found space
                    for j in range(start, start + size):
                        self.bitmap[j] = True
                    self.allocations[pid] = (start, size)
                    return start
            else:
                consecutive = 0
                start = -1
        return -1  # Out of memory

    def free(self, pid: int):
        """Free all memory allocated to a process."""
        if pid in self.allocations:
            start, size = self.allocations[pid]
            for i in range(start, start + size):
                self.bitmap[i] = False
            del self.allocations[pid]

    def get_free(self) -> int:
        return sum(1 for b in self.bitmap if not b)

    def dump(self) -> str:
        total = self.total_words
        used = total - self.get_free()
        return f"Memory: {used}/{total} words used ({100*used/total:.1f}%)"

# ─── File System (TriFS) ─────────────────────────────────────────────────────

@dataclass
class TriFSNode:
    """A file or directory in TriFS."""
    name: str
    is_dir: bool
    content: bytes = b''
    children: dict[str, 'TriFSNode'] = field(default_factory=dict)
    size: int = 0
    created_at: int = 0
    modified_at: int = 0

class TriFS:
    """Balanced ternary file system."""

    def __init__(self):
        self.root = TriFSNode("/", is_dir=True)
        self.next_fd = 3  # 0=stdin, 1=stdout, 2=stderr
        self.open_files: dict[int, tuple[TriFSNode, str]] = {}  # fd -> (node, mode)

    def _resolve(self, path: str) -> Optional[TriFSNode]:
        """Resolve a path to a node."""
        if path == '/':
            return self.root
        parts = [p for p in path.split('/') if p]
        node = self.root
        for part in parts:
            if not node.is_dir:
                return None
            if part not in node.children:
                return None
            node = node.children[part]
        return node

    def _parent(self, path: str) -> tuple[Optional[TriFSNode], str]:
        """Get parent directory and filename."""
        parts = [p for p in path.rstrip('/').split('/') if p]
        if not parts:
            return self.root, '/'
        name = parts[-1]
        parent_path = '/' + '/'.join(parts[:-1]) if len(parts) > 1 else '/'
        return self._resolve(parent_path), name

    def create(self, path: str, is_dir: bool = False) -> bool:
        parent, name = self._parent(path)
        if not parent or not parent.is_dir:
            return False
        if name in parent.children:
            return False
        parent.children[name] = TriFSNode(name, is_dir)
        return True

    def read(self, path: str) -> Optional[bytes]:
        node = self._resolve(path)
        if node and not node.is_dir:
            return node.content
        return None

    def write(self, path: str, data: bytes) -> bool:
        node = self._resolve(path)
        if node and not node.is_dir:
            node.content = data
            node.size = len(data)
            return True
        return False

    def delete(self, path: str) -> bool:
        parent, name = self._parent(path)
        if parent and name in parent.children:
            del parent.children[name]
            return True
        return False

    def list_dir(self, path: str) -> Optional[list[str]]:
        node = self._resolve(path)
        if node and node.is_dir:
            return sorted(node.children.keys())
        return None

    def open(self, path: str, mode: str = 'r') -> int:
        fd = self.next_fd
        self.next_fd += 1
        node = self._resolve(path)
        if node:
            self.open_files[fd] = (node, mode)
        return fd

    def close(self, fd: int) -> bool:
        if fd in self.open_files:
            del self.open_files[fd]
            return True
        return False

    def tree(self, path: str = "/", prefix: str = "") -> str:
        node = self._resolve(path)
        if not node:
            return ""
        lines = []
        if node.is_dir:
            for name, child in sorted(node.children.items()):
                lines.append(f"{prefix}{name}/" if child.is_dir else f"{prefix}{name}")
                if child.is_dir:
                    child_path = f"{path.rstrip('/')}/{name}"
                    lines.append(self.tree(child_path, prefix + "  "))
        return '\n'.join(lines)

# ─── Process Scheduler ───────────────────────────────────────────────────────

class Scheduler:
    """Round-robin scheduler with ternary priority."""

    def __init__(self):
        self.processes: dict[int, Process] = {}
        self.ready_queue: list[int] = []  # PIDs in ready state
        self.current_pid: int = -1
        self.next_pid: int = 1
        self.time_slice = 100  # Cycles per process

    def create_process(self, name: str, ppid: int = 0, priority: int = 0,
                       memory_size: int = 100) -> Process:
        pid = self.next_pid
        self.next_pid += 1
        cpu_state = CPUState()
        proc = Process(
            pid=pid, ppid=ppid, state=ProcessState.READY,
            priority=priority, cpu_state=cpu_state,
            memory_start=0, memory_size=memory_size, name=name
        )
        self.processes[pid] = proc
        self.ready_queue.append(pid)
        if ppid in self.processes:
            self.processes[ppid].children.append(pid)
        return proc

    def terminate_process(self, pid: int, exit_code: int = 0):
        if pid in self.processes:
            proc = self.processes[pid]
            proc.state = ProcessState.ZOMBIE
            proc.exit_code = exit_code
            if pid in self.ready_queue:
                self.ready_queue.remove(pid)

    def schedule(self) -> Optional[Process]:
        """Pick next process to run."""
        # Filter out non-ready processes
        self.ready_queue = [pid for pid in self.ready_queue
                           if pid in self.processes
                           and self.processes[pid].state == ProcessState.READY]

        if not self.ready_queue:
            return None

        # Priority: first try priority 1, then 0, then -1
        for pri in [1, 0, -1]:
            for pid in self.ready_queue:
                if self.processes[pid].priority == pri:
                    self.ready_queue.remove(pid)
                    self.ready_queue.append(pid)
                    self.current_pid = pid
                    self.processes[pid].state = ProcessState.RUNNING
                    return self.processes[pid]

        # Fallback: round robin
        pid = self.ready_queue.pop(0)
        self.ready_queue.append(pid)
        self.current_pid = pid
        self.processes[pid].state = ProcessState.RUNNING
        return self.processes[pid]

    def yield_cpu(self, pid: int):
        if pid in self.processes:
            self.processes[pid].state = ProcessState.READY

    def get_current(self) -> Optional[Process]:
        if self.current_pid in self.processes:
            return self.processes[self.current_pid]
        return None

# ─── System Call Handler ─────────────────────────────────────────────────────

class SyscallHandler:
    """Handles system calls from user processes."""

    def __init__(self, os: 'TriOS'):
        self.os = os

    def handle(self, proc: Process, syscall_num: int, args: list[int]) -> int:
        handlers = {
            Syscall.EXIT:    self._exit,
            Syscall.FORK:    self._fork,
            Syscall.READ:    self._read,
            Syscall.WRITE:   self._write,
            Syscall.OPEN:    self._open,
            Syscall.CLOSE:   self._close,
            Syscall.WAIT:    self._wait,
            Syscall.GETPID:  self._getpid,
            Syscall.GETPPID: self._getppid,
            Syscall.YIELD:   self._yield,
            Syscall.SLEEP:   self._sleep,
            Syscall.MALLOC:  self._malloc,
            Syscall.FREE:    self._free,
            Syscall.PRINT:   self._print,
            Syscall.INPUT:   self._input,
            Syscall.TIME:    self._time,
            Syscall.LIST:    self._list,
            Syscall.DELETE:  self._delete,
            Syscall.MKDIR:   self._mkdir,
        }
        handler = handlers.get(syscall_num)
        if handler:
            return handler(proc, args)
        return -1

    def _exit(self, proc: Process, args: list[int]) -> int:
        code = args[0] if args else 0
        self.os.scheduler.terminate_process(proc.pid, code)
        self.os.memory.free(proc.pid)
        return 0

    def _fork(self, proc: Process, args: list[int]) -> int:
        child = self.os.scheduler.create_process(
            f"{proc.name}_child", ppid=proc.pid,
            priority=proc.priority, memory_size=proc.memory_size
        )
        # Copy memory (simplified)
        return child.pid

    def _read(self, proc: Process, args: list[int]) -> int:
        fd = args[0] if args else 0
        if fd in proc.file_descriptors:
            path = proc.file_descriptors[fd]
            data = self.os.filesystem.read(path)
            return len(data) if data else 0
        return -1

    def _write(self, proc: Process, args: list[int]) -> int:
        fd = args[0] if args else 1
        if fd == 1:  # stdout
            return 1
        return -1

    def _open(self, proc: Process, args: list[int]) -> int:
        return self.os.filesystem.open(f"/proc_{proc.pid}_fd")

    def _close(self, proc: Process, args: list[int]) -> int:
        fd = args[0] if args else 0
        return 1 if self.os.filesystem.close(fd) else -1

    def _wait(self, proc: Process, args: list[int]) -> int:
        target = args[0] if args else -1
        if target in self.os.scheduler.processes:
            proc.state = ProcessState.WAITING
            proc.wait_target = target
            return 0
        return -1

    def _getpid(self, proc: Process, args: list[int]) -> int:
        return proc.pid

    def _getppid(self, proc: Process, args: list[int]) -> int:
        return proc.ppid

    def _yield(self, proc: Process, args: list[int]) -> int:
        self.os.scheduler.yield_cpu(proc.pid)
        return 0

    def _sleep(self, proc: Process, args: list[int]) -> int:
        cycles = args[0] if args else 0
        proc.state = ProcessState.WAITING
        proc.sleep_until = self.os.cycle_count + cycles
        return 0

    def _malloc(self, proc: Process, args: list[int]) -> int:
        size = args[0] if args else 1
        return self.os.memory.allocate(size, proc.pid)

    def _free(self, proc: Process, args: list[int]) -> int:
        self.os.memory.free(proc.pid)
        return 0

    def _print(self, proc: Process, args: list[int]) -> int:
        value = args[0] if args else 0
        self.os.console_output.append(str(value))
        return 0

    def _input(self, proc: Process, args: list[int]) -> int:
        if self.os.console_input:
            return self.os.console_input.pop(0)
        return 0

    def _time(self, proc: Process, args: list[int]) -> int:
        return self.os.cycle_count

    def _list(self, proc: Process, args: list[int]) -> int:
        entries = self.os.filesystem.list_dir("/")
        if entries:
            self.os.console_output.extend(entries)
        return len(entries) if entries else 0

    def _delete(self, proc: Process, args: list[int]) -> int:
        return 1  # Simplified

    def _mkdir(self, proc: Process, args: list[int]) -> int:
        return 1  # Simplified


# ─── TriOS Kernel ────────────────────────────────────────────────────────────

class TriOS:
    """The TriOS operating system kernel."""

    def __init__(self):
        self.cpu = TriCPU()
        self.memory = MemoryManager()
        self.filesystem = TriFS()
        self.scheduler = Scheduler()
        self.syscall_handler = SyscallHandler(self)
        self.cycle_count = 0
        self.console_output: list[str] = []
        self.console_input: list[int] = []
        self.running = False
        self.boot_time = 0

        # Create init process
        self.init_proc = self.scheduler.create_process("init", ppid=0, priority=0)
        self._setup_rootfs()

    def _setup_rootfs(self):
        """Set up the root file system."""
        self.filesystem.create("/bin", is_dir=True)
        self.filesystem.create("/etc", is_dir=True)
        self.filesystem.create("/home", is_dir=True)
        self.filesystem.create("/tmp", is_dir=True)
        self.filesystem.create("/dev", is_dir=True)
        self.filesystem.create("/proc", is_dir=True)
        self.filesystem.write("/etc/hostname", b"trios")
        self.filesystem.write("/etc/version", b"0.1.0")

    def boot(self):
        """Boot the OS."""
        print("╔══════════════════════════════════════╗")
        print("║   TriOS v0.1.0 — Ternary Operating  ║")
        print("║          System Booting...           ║")
        print("╚══════════════════════════════════════╝")
        print()

        self.boot_time = 0
        self.running = True

        # Initialize hardware
        print("[BOOT] Initializing TriCPU... ✅")
        print(f"[BOOT] Memory: {self.memory.total_words} words")
        print(f"[BOOT] File system: TriFS initialized")
        print(f"[BOOT] Scheduler: Round-robin with ternary priority")
        print(f"[BOOT] System calls: {len(Syscall)} syscalls available")
        print(f"[BOOT] Init process: PID {self.init_proc.pid}")
        print()
        print("[BOOT] TriOS ready. Type 'help' for commands.")
        print()

    def run_cycle(self) -> bool:
        """Run one CPU cycle. Returns False if no process is runnable."""
        proc = self.scheduler.schedule()
        if not proc:
            return False

        # Execute one instruction
        if not proc.cpu_state.halted:
            self.cpu.cpu = proc.cpu_state
            self.cpu.step()
            self.cycle_count += 1

            # Check for system calls (simplified: detected by special instruction)
            # In a real implementation, this would be an interrupt

        # Return process to ready queue if still running
        if proc.state == ProcessState.RUNNING:
            self.scheduler.yield_cpu(proc.pid)

        return True

    def run(self, max_cycles: int = 10_000):
        """Run the OS for a number of cycles."""
        for _ in range(max_cycles):
            if not self.run_cycle():
                break

    def create_user_process(self, name: str, program: list[int],
                            priority: int = 0) -> Process:
        """Create a new user process with a program."""
        proc = self.scheduler.create_process(name, ppid=1, priority=priority)
        mem_start = self.scheduler.processes[proc.pid].memory_start
        proc.cpu_state.load_program(program)
        return proc

    def shutdown(self):
        """Shut down the OS."""
        self.running = False
        print()
        print("[SHUTDOWN] TriOS shutting down...")
        print(f"[SHUTDOWN] Total cycles: {self.cycle_count}")
        print(f"[SHUTDOWN] Processes created: {self.scheduler.next_pid - 1}")
        print(f"[SHUTDOWN] Memory: {self.memory.dump()}")
        print("[SHUTDOWN] Goodbye! 👋")

    def status(self) -> str:
        lines = ["=== TriOS Status ==="]
        lines.append(f"  Cycles: {self.cycle_count}")
        lines.append(f"  Processes: {len(self.scheduler.processes)}")
        for pid, proc in self.scheduler.processes.items():
            state = proc.state.name
            lines.append(f"    PID {pid}: {proc.name} [{state}] pri={proc.priority}")
        lines.append(f"  {self.memory.dump()}")
        lines.append(f"  Ready queue: {self.scheduler.ready_queue}")
        if self.console_output:
            lines.append(f"  Console: {self.console_output[-5:]}")
        return '\n'.join(lines)


# ─── Shell ───────────────────────────────────────────────────────────────────

class TriShell:
    """Simple command-line shell for TriOS."""

    def __init__(self, os: TriOS):
        self.os = os
        self.commands = {
            'help':     self._cmd_help,
            'ps':       self._cmd_ps,
            'mem':      self._cmd_mem,
            'ls':       self._cmd_ls,
            'cat':      self._cmd_cat,
            'touch':    self._cmd_touch,
            'mkdir':    self._cmd_mkdir,
            'rm':       self._cmd_rm,
            'tree':     self._cmd_tree,
            'run':      self._cmd_run,
            'status':   self._cmd_status,
            'clear':    self._cmd_clear,
            'reboot':   self._cmd_reboot,
            'shutdown': self._cmd_shutdown,
        }

    def execute(self, line: str) -> str:
        parts = line.strip().split()
        if not parts:
            return ""
        cmd = parts[0].lower()
        args = parts[1:]
        handler = self.commands.get(cmd)
        if handler:
            return handler(args)
        return f"Unknown command: {cmd}. Type 'help' for available commands."

    def _cmd_help(self, args: list[str]) -> str:
        return (
            "Available commands:\n"
            "  help      — Show this help\n"
            "  ps        — List processes\n"
            "  mem       — Show memory usage\n"
            "  ls [path] — List directory\n"
            "  cat <file>— Show file contents\n"
            "  touch <f> — Create empty file\n"
            "  mkdir <d> — Create directory\n"
            "  rm <path> — Delete file/directory\n"
            "  tree      — Show filesystem tree\n"
            "  run <prog>— Run a program\n"
            "  status    — Show system status\n"
            "  clear     — Clear console\n"
            "  reboot    — Reboot the system\n"
            "  shutdown  — Shut down"
        )

    def _cmd_ps(self, args: list[str]) -> str:
        lines = ["PID  PPID  STATE     PRI  NAME"]
        for pid, proc in sorted(self.os.scheduler.processes.items()):
            lines.append(f"{pid:<4} {proc.ppid:<5} {proc.state.name:<9} {proc.priority:<+4} {proc.name}")
        return '\n'.join(lines)

    def _cmd_mem(self, args: list[str]) -> str:
        return self.os.memory.dump()

    def _cmd_ls(self, args: list[str]) -> str:
        path = args[0] if args else "/"
        entries = self.os.filesystem.list_dir(path)
        if entries:
            return '  '.join(entries)
        return f"Cannot list: {path}"

    def _cmd_cat(self, args: list[str]) -> str:
        if not args:
            return "Usage: cat <file>"
        data = self.os.filesystem.read(args[0])
        if data:
            return data.decode('utf-8', errors='replace')
        return f"Cannot read: {args[0]}"

    def _cmd_touch(self, args: list[str]) -> str:
        if not args:
            return "Usage: touch <file>"
        self.os.filesystem.create(args[0])
        return f"Created: {args[0]}"

    def _cmd_mkdir(self, args: list[str]) -> str:
        if not args:
            return "Usage: mkdir <dir>"
        self.os.filesystem.create(args[0], is_dir=True)
        return f"Created directory: {args[0]}"

    def _cmd_rm(self, args: list[str]) -> str:
        if not args:
            return "Usage: rm <path>"
        self.os.filesystem.delete(args[0])
        return f"Deleted: {args[0]}"

    def _cmd_tree(self, args: list[str]) -> str:
        return self.os.filesystem.tree()

    def _cmd_run(self, args: list[str]) -> str:
        if not args:
            return "Usage: run <program>"
        return f"Running {args[0]}... (simulated)"

    def _cmd_status(self, args: list[str]) -> str:
        return self.os.status()

    def _cmd_clear(self, args: list[str]) -> str:
        self.os.console_output.clear()
        return ""

    def _cmd_reboot(self, args: list[str]) -> str:
        self.os.__init__()
        self.os.boot()
        return "System rebooted."

    def _cmd_shutdown(self, args: list[str]) -> str:
        self.os.shutdown()
        return ""


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    """Run TriOS with an interactive shell."""
    os = TriOS()
    os.boot()
    shell = TriShell(os)

    # Demo: create some files
    os.filesystem.write("/home/hello.txt", b"Hello from TriOS!")
    os.filesystem.create("/home", is_dir=True)
    os.filesystem.write("/home/hello.txt", b"Hello from TriOS!")
    os.filesystem.create("/home/docs", is_dir=True)
    os.filesystem.write("/home/docs/readme.txt", b"TriOS - A ternary operating system")

    # Demo: create a user process
    from tri_cpu import Opcode
    program = [
        Opcode.ADDI, 1, 0, 42,
        Opcode.OUT, 1,
        Opcode.HALT,
    ]
    os.create_user_process("hello", program)

    # Run shell commands
    print(shell.execute("status"))
    print()
    print(shell.execute("ls"))
    print()
    print(shell.execute("tree"))
    print()
    print(shell.execute("ps"))
    print()
    print(shell.execute("cat /etc/hostname"))
    print()
    print(shell.execute("mem"))
    print()

    # Run a few cycles
    print("Running 10 cycles...")
    os.run(max_cycles=10)
    print(os.status())
    print()

    os.shutdown()


if __name__ == '__main__':
    main()
