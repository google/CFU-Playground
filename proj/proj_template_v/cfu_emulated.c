#include <stdint.h>

uint32_t Cfu(uint32_t functionid, uint32_t rs1, uint32_t rs2)
{
  (void)functionid;
  (void)rs2;
  if (functionid == 0x1) {
    return rs2;
  }
  return rs1;
}



