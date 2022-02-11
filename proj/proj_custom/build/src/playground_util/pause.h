#ifndef _PLAYGROUND_PAUSE_H
#define _PLAYGROUND_PAUSE_H

#include <stddef.h>

// Busy wait a short while. Typically used to avoid overflowing UART send
// buffers
inline static void pause() {
#ifndef PLATFORM_sim
  for (size_t i = 0; i < 20000000; i++) {
    asm volatile("nop");
  }
#endif
}

#endif  // _PLAYGROUND_PAUSE_H