# Ternary Eco / Hardware reference

Two small **portable reference implementations** complement the browser demo. These are not a complete ESP32-S3 firmware or a synthesized FPGA design.

## C11 / ESP32-S3 reference

    cc -std=c11 -Wall -Wextra -Werror -pedantic \
       hardware/esp32s3/ternary_kernel.c \
       hardware/esp32s3/test_kernel.c -o /tmp/ternary-kernel-test
    /tmp/ternary-kernel-test

Files:
- esp32s3/ternary_kernel.h — API
- esp32s3/ternary_kernel.c — canonical 5-trit/byte codec and sparse signed dot product
- esp32s3/test_kernel.c — exhaustive lengths 0..128, invalid encodings and dot product test

Next: compile through ESP-IDF, measure on an actual ESP32-S3 board, verify against browser golden vectors. Host GCC compilation does not prove Xtensa firmware compatibility or device performance.

## FPGA / VHDL-2008

Use GHDL when available:

    ghdl -a --std=08 hardware/fpga/trit_add.vhd
    ghdl -a --std=08 hardware/fpga/tb_trit_add.vhd
    ghdl -e --std=08 tb_trit_add
    ghdl -r --std=08 tb_trit_add --assert-level=error --stop-time=120ns

The RTL encodes -1/0/+1 as signed 2-bit states (11/00/01), rejects 10 (-2), and performs Z3 addition. The testbench checks all 9 valid input combinations and one invalid encoding.

Next: compare bit-exact vectors with BilaTiny and Python, synthesize to a named board with timing and resource reports; do not treat simulation as a hardware result.

## Source links and licenses

See ../docs/REPRODUCIBILITY.md. External TIS, Trilang and Rusty Penguin implementations are linked as conceptual references; no third-party compiler or OS code is vendored here.
