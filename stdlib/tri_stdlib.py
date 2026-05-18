#!/usr/bin/env python3
"""
TriLib — Standard library for the TriCPU ecosystem.

Provides utility functions for:
  - Ternary math (GCD, LCM, power, factorial, fibonacci)
  - String manipulation
  - Sorting algorithms (ternary-adapted)
  - Number base conversions
  - Data structures (stack, queue, linked list)
"""

from __future__ import annotations

# ─── Ternary Math ────────────────────────────────────────────────────────────

def ternary_gcd(a: int, b: int) -> int:
    """Greatest common divisor using balanced ternary arithmetic."""
    a, b = abs(a), abs(b)
    while b:
        a, b = b, a % b
    return a


def ternary_lcm(a: int, b: int) -> int:
    """Least common multiple."""
    if a == 0 or b == 0:
        return 0
    return abs(a * b) // ternary_gcd(a, b)


def ternary_power(base: int, exp: int) -> int:
    """Fast exponentiation in balanced ternary."""
    if exp < 0:
        return 0  # Integer arithmetic
    result = 1
    while exp > 0:
        if exp % 2 == 1:
            result *= base
        base *= base
        exp //= 2
    return result


def ternary_factorial(n: int) -> int:
    """Factorial using balanced ternary multiplication."""
    if n < 0:
        return 0
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result


def ternary_fibonacci(n: int) -> int:
    """Nth Fibonacci number using matrix exponentiation."""
    if n <= 0:
        return 0
    if n == 1:
        return 1

    def mat_mul(A, B):
        return [
            [A[0][0]*B[0][0] + A[0][1]*B[1][0], A[0][0]*B[0][1] + A[0][1]*B[1][1]],
            [A[1][0]*B[0][0] + A[1][1]*B[1][0], A[1][0]*B[0][1] + A[1][1]*B[1][1]],
        ]

    def mat_pow(M, p):
        result = [[1, 0], [0, 1]]
        while p > 0:
            if p % 2 == 1:
                result = mat_mul(result, M)
            M = mat_mul(M, M)
            p //= 2
        return result

    M = [[1, 1], [1, 0]]
    result = mat_pow(M, n - 1)
    return result[0][0]


def is_ternary_prime(n: int) -> bool:
    """Primality test for balanced ternary integers."""
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True


# ─── Base Conversions ────────────────────────────────────────────────────────

def int_to_ternary_string(n: int, width: int = 9) -> str:
    """Convert integer to balanced ternary string."""
    if n == 0:
        return '0' * width if width else '0'
    trits = []
    negative = n < 0
    n = abs(n)
    while n:
        trits.append(str(n % 3))
        n //= 3
    result = ''.join(reversed(trits))
    if width:
        result = result.zfill(width)
    return '-' + result if negative else result


def ternary_string_to_int(s: str) -> int:
    """Parse balanced ternary string to integer."""
    s = s.strip()
    negative = s.startswith('-')
    if negative:
        s = s[1:]
    mapping = {'T': -1, 't': -1, '0': 0, '1': 1}
    result = 0
    for ch in s:
        result = result * 3 + mapping.get(ch, 0)
    return -result if negative else result


def decimal_to_balanced_ternary(n: int) -> str:
    """Convert decimal to balanced ternary representation."""
    if n == 0:
        return '0'
    trits = []
    while n != 0:
        rem = n % 3
        n //= 3
        if rem == 2:
            rem = -1
            n += 1
        trits.append(rem)
    chars = {-1: 'T', 0: '0', 1: '1'}
    return ''.join(chars[t] for t in reversed(trits))


def balanced_ternary_to_decimal(s: str) -> int:
    """Convert balanced ternary string to decimal."""
    mapping = {'T': -1, 't': -1, '0': 0, '1': 1}
    result = 0
    for ch in s:
        result = result * 3 + mapping.get(ch, 0)
    return result


# ─── Sorting (Ternary-Adapted) ──────────────────────────────────────────────

def ternary_sort(arr: list[int]) -> list[int]:
    """Sort using comparison in balanced ternary."""
    return sorted(arr)


def ternary_merge_sort(arr: list[int]) -> list[int]:
    """Merge sort adapted for ternary comparison."""
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = ternary_merge_sort(arr[:mid])
    right = ternary_merge_sort(arr[mid:])
    return _ternary_merge(left, right)


def _ternary_merge(left: list[int], right: list[int]) -> list[int]:
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        # Ternary comparison: -1, 0, 1
        cmp = _ternary_compare(left[i], right[j])
        if cmp <= 0:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result


def _ternary_compare(a: int, b: int) -> int:
    """Balanced ternary comparison: returns -1, 0, or 1."""
    if a < b:
        return -1
    elif a > b:
        return 1
    return 0


# ─── Data Structures ────────────────────────────────────────────────────────

class TernaryStack:
    """Stack with ternary overflow detection."""

    def __init__(self, max_size: int = 100):
        self.data: list[int] = []
        self.max_size = max_size

    def push(self, value: int) -> bool:
        if len(self.data) >= self.max_size:
            return False
        self.data.append(value)
        return True

    def pop(self) -> int:
        if not self.data:
            raise IndexError("Stack underflow")
        return self.data.pop()

    def peek(self) -> int:
        if not self.data:
            raise IndexError("Stack empty")
        return self.data[-1]

    def is_empty(self) -> bool:
        return len(self.data) == 0

    def size(self) -> int:
        return len(self.data)


class TernaryQueue:
    """Circular queue with balanced ternary capacity."""

    def __init__(self, capacity: int = 27):
        self.capacity = capacity
        self.data: list[int] = [0] * capacity
        self.head = 0
        self.tail = 0
        self.count = 0

    def enqueue(self, value: int) -> bool:
        if self.count >= self.capacity:
            return False
        self.data[self.tail] = value
        self.tail = (self.tail + 1) % self.capacity
        self.count += 1
        return True

    def dequeue(self) -> int:
        if self.count == 0:
            raise IndexError("Queue empty")
        value = self.data[self.head]
        self.head = (self.head + 1) % self.capacity
        self.count -= 1
        return value

    def is_empty(self) -> bool:
        return self.count == 0

    def is_full(self) -> bool:
        return self.count == self.capacity


class TernaryLinkedList:
    """Linked list with ternary node values."""

    class Node:
        __slots__ = ['value', 'next']
        def __init__(self, value: int):
            self.value = value
            self.next: Optional['TernaryLinkedList.Node'] = None

    def __init__(self):
        self.head: Optional[TernaryLinkedList.Node] = None
        self.length = 0

    def prepend(self, value: int):
        node = self.Node(value)
        node.next = self.head
        self.head = node
        self.length += 1

    def append(self, value: int):
        node = self.Node(value)
        if not self.head:
            self.head = node
        else:
            current = self.head
            while current.next:
                current = current.next
            current.next = node
        self.length += 1

    def to_list(self) -> list[int]:
        result = []
        current = self.head
        while current:
            result.append(current.value)
            current = current.next
        return result


# ─── Demo ────────────────────────────────────────────────────────────────────

def main():
    print("=== TriLib Standard Library Demo ===")
    print()

    # Ternary math
    print("Ternary Math:")
    print(f"  GCD(48, 18) = {ternary_gcd(48, 18)}")
    print(f"  LCM(12, 15) = {ternary_lcm(12, 15)}")
    print(f"  2^10 = {ternary_power(2, 10)}")
    print(f"  10! = {ternary_factorial(10)}")
    print(f"  fib(20) = {ternary_fibonacci(20)}")
    print(f"  is_prime(97) = {is_ternary_prime(97)}")
    print()

    # Base conversions
    print("Base Conversions:")
    for n in [0, 1, -1, 5, -5, 42, -42, 100, -100]:
        bt = decimal_to_balanced_ternary(n)
        back = balanced_ternary_to_decimal(bt)
        print(f"  {n:>4} decimal = {bt:>8} balanced ternary = {back:>4} decimal")
    print()

    # Sorting
    print("Sorting:")
    arr = [5, -3, 0, 8, -1, 4, -7, 2]
    print(f"  Input:  {arr}")
    print(f"  Sorted: {ternary_sort(arr)}")
    print(f"  Merge:  {ternary_merge_sort(arr)}")
    print()

    # Data structures
    print("Data Structures:")
    stack = TernaryStack()
    for v in [1, -1, 0, 5, -3]:
        stack.push(v)
    print(f"  Stack: {stack.data}")
    print(f"  Pop: {stack.pop()}, remaining: {stack.data}")

    queue = TernaryQueue(5)
    for v in [1, 2, 3]:
        queue.enqueue(v)
    print(f"  Queue: count={queue.count}, dequeue: {queue.dequeue()}")

    ll = TernaryLinkedList()
    for v in [1, -1, 0]:
        ll.append(v)
    print(f"  LinkedList: {ll.to_list()}")


if __name__ == '__main__':
    main()
