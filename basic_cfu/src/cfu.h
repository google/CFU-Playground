// This inline function emits the correct assembly sequence to execute a custom
// instruction.
  // We need to emit a custom instruction to do the decoding.
  // The custom instruction takes the size of the string as an immediate, the
  // address of the bytes in a register, and sets a uint32 in a register.
  // Since it's a custom instruction, we don't have any compiler/assembler
  // support to use the built-in assembly/C/C++ linkage facilities.  Instead,
  // the instruction is custom encoded using the .long below, and explicitly
  // move the to/from the hard-coded x10 and x11 registers into the ones
  // picked by the compiler for decoded and bytes.  I use asm hints to tell
  // the compiler that I'm using x10 and x11 in this way.

inline uint32_t RunCustomInstruction0(uint32_t value1, uint32_t value2) {
  uint32_t result = 0;
  asm volatile(
      "mv x10, %1\n"
      "mv x11, %2\n"
      ".long 0x06b5050b\n"      // fn = 3'b000
      "mv %0, x10\n"
      : [result] "=r"(result)
      : [value1] "r"(value1), [value2] "r"(value2)
      : "x10", "x11");
  return result;
}


inline uint32_t RunCustomInstruction1(uint32_t value1, uint32_t value2) {
  uint32_t result = 0;
  asm volatile(
      "mv x10, %1\n"
      "mv x11, %2\n"
      ".long 0x06b5150b\n"      // fn = 3'b001
      "mv %0, x10\n"
      : [result] "=r"(result)
      : [value1] "r"(value1), [value2] "r"(value2)
      : "x10", "x11");
  return result;
}


inline uint32_t RunCustomInstruction2(uint32_t value1, uint32_t value2) {
  uint32_t result = 0;
  asm volatile(
      "mv x10, %1\n"
      "mv x11, %2\n"
      ".long 0x06b5250b\n"      // fn = 3'b010
      "mv %0, x10\n"
      : [result] "=r"(result)
      : [value1] "r"(value1), [value2] "r"(value2)
      : "x10", "x11");
  return result;
}



