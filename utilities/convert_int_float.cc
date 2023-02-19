#include <stdint.h>
#include <stdio.h>

#define N_TRANSFORMS 11
int32_t transforms[N_TRANSFORMS] = {
    1042039934, 1062792856, 911283909, 865465390, 788076929, 834594960,
    860604858,  848206996,  892220434, 890493883, 812697982,
};

int main() {
  printf("Hello World\n");
  for (size_t i = 0; i < N_TRANSFORMS; ++i) {
    int32_t n = transforms[i];
    float nf = *((float*)&n);
    printf("n: %df, nf: %.6f\n", n, nf);
  }
  return 0;
}
