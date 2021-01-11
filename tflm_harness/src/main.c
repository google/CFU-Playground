#include <generated/csr.h>
#include <hw/common.h>
#include <console.h>
#include <stdio.h>
#include <string.h>
#include <irq.h>
#include <uart.h>

#include <i2c.h>

#include "tflite.h"
#include "perf.h"

void isr(void)
{
        __attribute__((unused)) unsigned int irqs;

        irqs = irq_pending() & irq_getmask();

        if(irqs & (1 << UART_INTERRUPT)) {
                uart_isr();
                leds_out_write(leds_out_read() ^ 0x100);
        }
}



void detect() {
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



int main(void) {
    irq_setmask(0);
    irq_setie(1);
    uart_init();

    printf("Hello, %s!\n", "World");

    // Tflm init
    puts("initTfLite()");
    initTfLite();

    // ONCE_AND_QUIT
    load_zeros();
    puts("Running one inference");
    detect();
    puts("Done");
    return(0);
}

