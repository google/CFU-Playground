// The donut code with fixed-point arithmetic; no sines, cosines, square roots, or anything.
// a1k0n 2020
// Code from: https://gist.github.com/a1k0n/80f48aa8911fffd805316b8ba8f48e83
// For more info:
// - https://www.a1k0n.net/2011/07/20/donut-math.html
// - https://www.youtube.com/watch?v=DEqXNfs_HhY

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <cfu.h>
#include <perf.h>

#include <console.h>

//
// ACCELERATED VERSION
//
// using these two Custom Instructions
//    added via CFU (Custom Function Unit)
//
#define MULTSHIFT10(a,b)     ((int)cfu_op(0, 0, (a), (b)))
#define CFUMUL(a,b)          ((int)cfu_op(1, 1, (a), (b)))

#define R(mul,shift,x,y) \
  _=x; \
  x -= CFUMUL(mul,y)>>shift; \
  y += CFUMUL(mul,_)>>shift; \
  _ = 3145728-CFUMUL(x,x)-CFUMUL(y,y)>>11; \
  x = CFUMUL(x,_)>>10; \
  y = CFUMUL(y,_)>>10;


static signed char b[1760], z[1760];

#ifdef OPT_LINK_CODE_IN_SRAM
void donut(void) __attribute__((section(".ramtext")));
#else
void donut(void);
#endif


void donut(void) {
  int sA=1024,cA=0,sB=1024,cB=0,_;
  puts("\nPress any key to exit.  Accelerated version.\n");
  for (;;) {
    unsigned start_cycle = perf_get_mcycle();
    memset(b, 32, 1760);  // text buffer
    memset(z, 127, 1760);   // z buffer
    int sj=0, cj=1024;
    for (int j = 0; j < 90; j++) {
      int si = 0, ci = 1024;  // sine and cosine of angle i
      for (int i = 0; i < 324; i++) {
        int R1 = 1, R2 = 2048, K2 = 5120*1024;

        int x0 = CFUMUL(R1,cj) + R2,
            x1 = MULTSHIFT10(ci,x0),
            x2 = MULTSHIFT10(cA,sj),
            x3 = MULTSHIFT10(si,x0),
            x4 = CFUMUL(R1,x2) - MULTSHIFT10(sA,x3),
            x5 = MULTSHIFT10(sA,sj),
            x6 = K2 + (CFUMUL(R1,x5)<<10) + CFUMUL(cA,x3),
            x7 = MULTSHIFT10(cj,si),
            x8 = CFUMUL(cB,x1) - CFUMUL(sB,x4),
            x = 40 + CFUMUL(30,x8)/x6,
            x9 = CFUMUL(cB,x4) + CFUMUL(sB,x1),
            y = 12 + CFUMUL(15,x9)/x6;
            int xx = MULTSHIFT10(cj,sB);
            int N =   (-CFUMUL(cA,x7) - cB*((-MULTSHIFT10(sA,x7))      + x2) - CFUMUL(ci,xx) >> 10) - x5 >> 7;


        int o = x + CFUMUL(80,y);
        signed char zz = (x6-K2)>>15;
        if (22 > y && y > 0 && x > 0 && 80 > x && zz < z[o]) {
          z[o] = zz;
          b[o] = ".,-~:;=!*#$@"[N > 0 ? N : 0];
        }
        R(5, 8, ci, si)  // rotate i
      }
      R(9, 7, cj, sj)  // rotate j
    }
    for (int k = 0; 1761 > k; k++)
      putchar(k % 80 ? b[k] : 10);
    R(5, 7, cA, sA);
    R(5, 8, cB, sB);
    if (readchar_nonblock()) {
        getchar();
        break;
    }
    unsigned end_cycle = perf_get_mcycle();
    printf("%d cycles\n", end_cycle - start_cycle);
    puts("\x1b[25A");
  }
}
