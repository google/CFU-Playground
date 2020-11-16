#include <generated/csr.h>
#include <hw/common.h>
#include <console.h>
#include <stdio.h>
#include <string.h>
#include <irq.h>
#include <uart.h>

#include <i2c.h>

#include "tflite.h"

void isr(void)
{
        __attribute__((unused)) unsigned int irqs;

        irqs = irq_pending() & irq_getmask();

        if(irqs & (1 << UART_INTERRUPT)) {
                uart_isr();
                leds_out_write(leds_out_read() ^ 0x100);
        }
}

#if 1

#define HM01B0_PIXEL_X_NUM 96
#define HM01B0_PIXEL_Y_NUM 96

#define FB_SIZE ((size_t)HM01B0_PIXEL_X_NUM * (size_t)HM01B0_PIXEL_Y_NUM)
uint8_t frame[FB_SIZE];


const char shades[16] = {
    ' ', '.', ',', '-', '+', '/', '1', 'r', 'n', 'x', 'L', '0', 'o', 'm', '*', '#'
};



void show_input() {
  int8_t *input = get_input();
  for (size_t in_y = 0; in_y < 96; in_y++) {
    char line[193];
    line[192] = 0;

    for (size_t in_x = 0; in_x < 96; in_x++) {
      int val = *input++;
      line[in_x*2]   = shades[16-(val+128+8)/16];
      line[in_x*2+1] = shades[16-(val+128+8)/16];
    }
    printf("%s\n", line);
  }
}

void detect() {
  show_input();

  int8_t person, no_person;
  printf("classifying");
  classify(&person, &no_person);
  printf("Person:    %d\nNot person: %d\n", person, no_person);
  if (person <= -30) {
    puts("*** No person found");
  } else if (person <= 30) {
    puts("*** Image has person like attributes");
  } else if (person <= 60) {
    puts("*** Might be a person");
  } else {
    puts("*** PERSON");
  }

}




// Outputs data as 244 lines of 324 base64 encoded bytes
/*
static const char *b64_table = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
static inline char b64_lookup(uint8_t n) {
  return b64_table[0x3f & n];
}
#define b64_line_len  (HM01B0_PIXEL_X_NUM / 3 * 4 + 1)
static char b64_buf[b64_line_len+1];
*/

extern int g_no_person_data_size, g_person_data_size;


int main(void) {
    irq_setmask(0);
    irq_setie(1);
    uart_init();

    printf("Hello, %s!\n", "World");
    printf("g_no_person_data_size: %d\n", g_no_person_data_size);
    printf("g_person_data_size: %d\n", g_person_data_size);

    // Tflm init
    puts("initTfLite()");
    initTfLite();
    
    while (1) {

        // Mirror the bytes back
        puts("\n\nMenu");
        puts("----");
        puts("4. Load Person example");
        puts("5. Load No Person example");
        puts("6. Detect");
        puts("> ");

        int c = readchar();
        putchar(c);
        putchar('\n');

        switch (c) {
            case '4': load_person(); break;
            case '5': load_no_person(); break;
            case '6': detect(); break;
            default: puts("???\n");
        }
    }
}

#endif

