#include <stdint.h>

uint32_t Cfu(uint32_t functionid, uint32_t rs1, uint32_t rs2)
{
  uint32_t s1=1, s2=1;

  for (uint32_t count = rs1; count > 0; --count) {
      uint32_t sum = s1 + s2;
      s1 = s2;
      s2 = sum;
  }

  return s2;
}



