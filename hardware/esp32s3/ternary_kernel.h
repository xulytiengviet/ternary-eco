/* Ternary Eco reference kernel. Compatible with C11; no ESP-IDF dependencies.
 * Host-tested on GCC. ESP32-S3 compilation, timing and power NOT yet verified. */
#ifndef TERNARY_ECO_KERNEL_H
#define TERNARY_ECO_KERNEL_H
#include <stddef.h>
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
/* Returns number of written bytes, or -1 on invalid input/capacity. */
int ternary_pack5(const int8_t *trits, size_t n, uint8_t *out, size_t out_cap);
/* Returns 0 on success, -1 for invalid byte, padding, length or capacity. */
int ternary_unpack5(const uint8_t *bytes, size_t nbytes, size_t ntrits,
                    int8_t *out, size_t out_cap);
/* Returns 0 on success; -1 for invalid arguments/domain/dimension.
 * For n <= 65535, accumulator cannot overflow int32_t with int16 input. */
int ternary_dot_s16(const int16_t *x, const int8_t *weights, size_t n,
                    int32_t *result);
#ifdef __cplusplus
}
#endif
#endif
