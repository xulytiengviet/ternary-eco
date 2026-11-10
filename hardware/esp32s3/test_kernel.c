#include "ternary_kernel.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
int main(void) {
    int8_t input[128] = {0}, restored[128] = {0};
    uint8_t packed[26] = {0};
    for (size_t n = 0; n <= 128; ++n) {
        for (size_t i = 0; i < n; ++i) input[i] = (int8_t)((i + n) % 3) - 1;
        const int count = ternary_pack5(input, n, packed, sizeof(packed));
        assert(count == (int)(n / 5u + (n % 5u != 0u)));
        memset(restored, 0, sizeof(restored));
        assert(ternary_unpack5(packed, (size_t)count, n, restored, sizeof(restored)) == 0);
        assert(memcmp(input, restored, n) == 0);
    }
    const int8_t five_neg[] = {-1,-1,-1,-1,-1};
    const int8_t five_pos[] = { 1, 1, 1, 1, 1};
    assert(ternary_pack5(five_neg, 5, packed, sizeof(packed)) == 1 && packed[0] == 0);
    assert(ternary_pack5(five_pos, 5, packed, sizeof(packed)) == 1 && packed[0] == 242);
    packed[0] = 243;
    assert(ternary_unpack5(packed, 1, 5, restored, sizeof(restored)) == -1);
    input[0] = 2;
    assert(ternary_pack5(input, 1, packed, sizeof(packed)) == -1);
    const int16_t x[] = {100,200,-100,300};
    const int8_t w[] = {1,0,-1,1};
    int32_t result = 0;
    assert(ternary_dot_s16(x,w,4,&result) == 0 && result == 500);
    const int8_t wrong[] = {1,0,2,1};
    assert(ternary_dot_s16(x,wrong,4,&result) == -1);
    puts("PASS: C11 pack5/unpack5 lengths 0..128 + sparse dot product");
    return 0;
}
