; Fibonacci Sequence — TriCPU Assembly
; Computes the first N Fibonacci numbers
; N is set in R1, results are output one by one

        .origin 0

        ADDI    R1, R0, 10       ; R1 = 10 (count of numbers to generate)
        ADDI    R2, R0, 0        ; R2 = 0 (fib(n-2))
        ADDI    R3, R0, 1        ; R3 = 1 (fib(n-1))

loop:   OUT     R2               ; Output current Fibonacci number
        ADD     R4, R2, R3       ; R4 = R2 + R3 (next Fibonacci)
        ADD     R2, R0, R3       ; R2 = R3 (shift window)
        ADD     R3, R0, R4       ; R3 = R4 (shift window)
        SUBI    R1, R1, 1        ; Decrement counter
        CMP     R1, R0           ; Compare with 0
        JN      loop             ; If counter > 0, continue

        HALT
