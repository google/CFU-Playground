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

#define multshift10(a,b)     ((int)cfu_op(0, 0, (a), (b)))
#define cfumul(a,b)          ((int)cfu_op(1, 1, (a), (b)))

#define R(mul,shift,x,y) \
  _=x; \
  x -= cfumul(mul,y)>>shift; \
  y += cfumul(mul,_)>>shift; \
  _ = 3145728-cfumul(x,x)-cfumul(y,y)>>11; \
  x = cfumul(x,_)>>10; \
  y = cfumul(y,_)>>10;

static signed char b[1760], z[1760];

#ifdef OPT_LINK_CODE_IN_SRAM
void donut(void) __attribute__((section(".ramtext")));
#else
void donut(void);
#endif


void donut(void) {
  int sA=1024,cA=0,sB=1024,cB=0,_;
  int R1 = 1, R2 = 2048, K2 = 5120*1024;
  puts("\nPress any key to exit.  Accelerated version.\n");
  for (;;) {
    unsigned start_cycle = perf_get_mcycle();
    memset(b, 32, 1760);  // text buffer
    memset(z, 127, 1760);   // z buffer
    int sj=0, cj=1024;
    for (int j = 0; j < 90; j++) {
      int si = 0, ci = 1024;  // sine and cosine of angle i
      for (int i = 0; i < 324; i++) {

        int x0 = cfumul(R1,cj) + R2,
            x1 = multshift10(ci,x0),
            x2 = multshift10(cA,sj),
            x3 = multshift10(si,x0),
            x4 = cfumul(R1,x2) - multshift10(sA,x3),
            x5 = multshift10(sA,sj),
            x6 = K2 + (cfumul(R1,x5)<<10) + cfumul(cA,x3),
            x7 = multshift10(cj,si),
            x8 = cfumul(cB,x1) - cfumul(sB,x4),
            x = 40 + cfumul(30,x8)/x6,
            x9 = cfumul(cB,x4) + cfumul(sB,x1),
            y = 12 + cfumul(15,x9)/x6;
            int xx = multshift10(cj,sB);
            int N =   (-cfumul(cA,x7) - cB*((-multshift10(sA,x7))      + x2) - cfumul(ci,xx) >> 10) - x5 >> 7;


        int o = x + cfumul(80,y);
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
