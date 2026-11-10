#include "ternary_kernel.h"
#include <limits.h>
#define MAX_DOT_TERMS 65535u

int ternary_pack5(const int8_t *trits, size_t n, uint8_t *out, size_t cap) {
    const size_t count = n / 5u + ((n % 5u) != 0u);
    if (count > (size_t)INT_MAX || cap < count) return -1;
    if (n > 0 && (!trits || !out)) return -1;
    for (size_t block = 0; block < count; ++block) {
        unsigned int byte = 0u;
        for (size_t j = 0; j < 5u; ++j) {
            const size_t idx = block * 5u + j;
            const int8_t t = idx < n ? trits[idx] : 0;
            if (t < -1 || t > 1) return -1;
            byte = byte * 3u + (unsigned int)(t + 1);
        }
        out[block] = (uint8_t)byte; /* Always <= 242 */
    }
    return (int)count;
}

int ternary_unpack5(const uint8_t *bytes, size_t nbytes, size_t ntrits,
                    int8_t *out, size_t cap) {
    const size_t expected = ntrits / 5u + ((ntrits % 5u) != 0u);
    if (nbytes != expected || cap < ntrits) return -1;
    if (nbytes > 0 && (!bytes || !out)) return -1;
    for (size_t block = 0; block < nbytes; ++block) {
        unsigned int byte = bytes[block];
        if (byte > 242u) return -1;
        int8_t digits[5];
        for (int j = 4; j >= 0; --j) {
            digits[j] = (int8_t)((int)(byte % 3u) - 1);
            byte /= 3u;
        }
        for (size_t j = 0; j < 5u; ++j) {
            const size_t idx = block * 5u + j;
            if (idx < ntrits) out[idx] = digits[j];
            else if (digits[j] != 0) return -1; /* Canonical padding. */
        }
    }
    return 0;
}

int ternary_dot_s16(const int16_t *x, const int8_t *w, size_t n, int32_t *result) {
    if (!result || n > MAX_DOT_TERMS || (n > 0 && (!x || !w))) return -1;
    int32_t sum = 0;
    for (size_t i = 0; i < n; ++i) {
        if (w[i] == 1) sum += (int32_t)x[i];
        else if (w[i] == -1) sum -= (int32_t)x[i];
        else if (w[i] != 0) return -1;
    }
    *result = sum;
    return 0;
}
