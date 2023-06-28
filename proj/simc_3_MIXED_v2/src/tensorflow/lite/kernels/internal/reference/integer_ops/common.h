#pragma once

#include <algorithm>
#include <cassert>
#include <cstdint>

template <typename IntegerType>
inline IntegerType rounding_divide_by_POT(IntegerType x, int exponent) {
  assert(exponent >= 0);
  assert(exponent <= 31);
  const IntegerType mask      = (1ll << exponent) - 1;
  const IntegerType zero      = 0;
  const IntegerType one       = 1;
  const IntegerType remainder = x & mask;
  const IntegerType threshold = (mask >> 1) + (((x < zero) ? ~0 : 0) & one);
  return (x >> exponent) + (((remainder > threshold) ? ~0 : 0) & one);
}

inline std::int32_t saturating_rounding_doubling_high_mul(std::int32_t a, std::int32_t b) {
  bool overflow = a == b && a == std::numeric_limits<std::int32_t>::min();
  std::int64_t a_64(a);
  std::int64_t b_64(b);
  std::int64_t ab_64        = a_64 * b_64;
  std::int32_t nudge        = ab_64 >= 0 ? (1 << 30) : (1 - (1 << 30));
  std::int32_t ab_x2_high32 = static_cast<std::int32_t>((ab_64 + nudge) / (1ll << 31));
  return overflow ? std::numeric_limits<std::int32_t>::max() : ab_x2_high32;
}

inline int32_t multiply_by_quant_mult(int32_t x, int32_t quantized_multiplier, int shift) {
  int left_shift  = shift > 0 ? shift : 0;
  int right_shift = shift > 0 ? 0 : -shift;
  return rounding_divide_by_POT(
      saturating_rounding_doubling_high_mul(x * (1 << left_shift), quantized_multiplier),
      right_shift);
}