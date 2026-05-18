; Factorial Calculator — TriCPU Assembly
; Computes n! for a given n
; Input: n is pre-loaded into R1
; Output: result is output via OUT instruction

        .origin 0

        ; R1 = 5 (compute 5!)
        ADDI    R1, R0, 5        ; R1 = 5 (counter)
        ADDI    R2, R0, 1        ; R2 = 1 (accumulator)

loop:   MUL     R3, R2, R1       ; R3 = R2 * R1
        ADD     R2, R0, R3       ; R2 = R3 (update accumulator)
        SUBI    R1, R1, 1        ; R1 = R1 - 1 (decrement counter)
        CMP     R1, R0           ; Compare R1 with 0
        JP      loop             ; If R1 > 0, continue loop

        OUT     R2               ; Output result (120)
        HALT
