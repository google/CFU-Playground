#include <generated/csr.h>
#include <hw/common.h>
#include <console.h>
#include <stdio.h>
#include <irq.h>
#include <uart.h>

#include "perf.h"
#include "riscv.h"
#include "cfu.h"


void isr(void)
{
	__attribute__((unused)) unsigned int irqs;

	irqs = irq_pending() & irq_getmask();

	if(irqs & (1 << UART_INTERRUPT)) {
		uart_isr();
                leds_out_write(leds_out_read() ^ 0x8);
        }
}


int get_char_val(char c)
{
        if (c >= '0' && c <= '9') return (int)(c - '0');
        if (c >= 'a' && c <= 'f') return (int)(c - 'a' + 10);
        if (c >= 'A' && c <= 'F') return (int)(c - 'A' + 10);
        return -1;
}

unsigned int readval()
{
        unsigned int retval = 0;
        do {
                char c = readchar();
                putchar(c);
                int v = get_char_val(c);
                if (v<0) {
                        putchar('\n');
                        return retval;
                } else {
                        retval = (retval<<4) + (unsigned int)v;
                }
        } while (1);
}


void __attribute__ ((noinline)) run_demo()
{
        puts("\n\nCFU TEST:");

        puts("Enter first operand value (in hexadecimal, no leading '0x'):");
        unsigned int v0 = readval();

        puts("Enter second operand value (in hexadecimal, no leading '0x'):");
        unsigned int v1 = readval();

        int r0 = cfu_op0_hw(v0, v1);    // byte sum
        int r1 = cfu_op1_hw(v0, v1);    // byte swap
        int r2 = cfu_op2_hw(v0, v1);    // bit reverse
        int r3 = cfu_op3_hw(v0, v1);    // fib

        puts("arg0        arg1        bytesum     byteswap    bitrev    fib");
        printf("0x%08x, 0x%08x: 0x%08x, 0x%08x, 0x%08x, 0x%08x\n", v0, v1, r0, r1, r2, r3);
        printf("  %08d,   %08d:   %08d,   %08d,   %08d,   %08d\n", v0, v1, r0, r1, r2, r3);
        puts("\n");
}

void __attribute__ ((noinline)) run_cfu()
{
        puts("\n\nCFU TEST:");
        puts("arg0        arg1        bytesum     byteswap    bitrev");
        for (int i=0; i<0x50505; i+=0x8103) {
            int v0 = cfu_op0_hw(i, i);    // byte sum
            int v1 = cfu_op1_hw(i, i);    // byte swap
            int v2 = cfu_op2_hw(i, i);    // bit reverse
            int v3 = cfu_op3_hw(i&63, i&63);    // fib
            printf("0x%08x, 0x%08x: 0x%08x, 0x%08x, 0x%08x, 0x%08x\n", i, i, v0, v1, v2, v3);
        }
        puts("\n");
}

void __attribute__ ((noinline)) compare_against_sw()
{
        puts("\n\nCFU:SW TEST:");
        puts("arg0        arg1            bytesum           byteswap         bitrev");
        unsigned count = 0;
        for (unsigned i=0; i<0x5050505; i+=0x7105) {
          for (unsigned j=0; j<0x5050505; j+=0xb103) {
            unsigned v0 = cfu_op0_hw(i, j);
            unsigned v1 = cfu_op1_hw(i, j);
            unsigned v2 = cfu_op2_hw(i, j);
            unsigned v3 = cfu_op3_hw(i&15, j&15);
            unsigned sw0 = cfu_op0_sw(i, j);
            unsigned sw1 = cfu_op1_sw(i, j);
            unsigned sw2 = cfu_op2_sw(i, j);
            unsigned sw3 = cfu_op3_sw(i&15, j&15);
            if (v0!=sw0 || v1!=sw1 || v2!=sw2 || v3!=sw3) {
                printf("0x%08x, 0x%08x: 0x%08x:0x%08x, 0x%08x:0x%08x, 0x%08x:0x%08x, 0x%08x:0x%08x <<=== MISMATCH!\n", 
                        i, j, v0, sw0, v1, sw1, v2, sw2, v3, sw3);
            }
            ++count;
            if ((count & 0xffff) == 0) printf("Ran %d comparisons....\n", count);
          }
        }
        printf("Ran %d comparisons.\n", count);
}

void show_menu(void)
{
    puts("\n\n");
    puts("0: switch to perf counter 0 and show value");
    puts("1: switch to perf counter 1 and show value");
    puts("e: enable current perf counter");
    puts("p: pause current perf counter");
    puts("z: zero-out current perf counter, and also zero-out mcycle");
    puts("m: show current value of mcycle (mcycle is not pausable)");
    puts("");
    puts("c: run preset CFU test (run fixed values through funct0, funct1, and funct2)");
    puts("d: interactive CFU test -- you supply the operands");
    puts("s: run test of CFU against software emulation");
    puts("");
    puts("?: show menu again");
    puts("\n");
}


int main(void) 
{
    const char hell[] = "Hello, World!";
    const char gibb[] = "Type some gibberish, watch the LEDs";

    leds_out_write(0xf);
    int leds_val = 0x0;


    irq_setmask(0);
    irq_setie(1);
    uart_init();

    for (int i=0; i<20 * 1000000; ++i) {
        if ((i & 0xfffff ) == 0) {
            leds_val += 0x1;
            leds_out_write(leds_val);
        }
    }

    puts(hell);
    puts(gibb);
    putchar('\n');

    
    int counter_num = 0;
    show_menu();
    while (1) {
        char c = readchar();
        putchar(c);
        // double up if odd
        if (c & 0x1) putchar(c);
        if (c == '?') {
            show_menu();
        }
        if (c == 'c') {
            run_cfu();
        }
        if (c == 'd') {
            run_demo();
        }
        if (c == 'z') {
            set_mcycle(0);
            set_counter_enable(counter_num, 0);
            set_counter(counter_num, 0);
            printf("\nzero-out mcycle and counter-%d\n", counter_num);
        }
        if (c == 'm') {
            printf("cycle: %u\n", get_mcycle());
        }
        if (c == 'e') {
            printf("nable perf counter %d\n", counter_num);
            set_counter_enable(counter_num, 1);
        }
        if (c == '0') {
            counter_num = 0;
            printf("-curr perf counter %d: %u\n", counter_num, get_counter(counter_num));
        }
        if (c == '1') {
            counter_num = 1;
            printf("-curr perf counter %d: %u\n", counter_num, get_counter(counter_num));
        }
        if (c == 'p') {
            printf("ause perf counter %d\n", counter_num);
            set_counter_enable(counter_num, 0);
        }
        if (c == 's') {
            printf("oftware comparison\n");
            compare_against_sw();
        }
        leds_val += 1;
        leds_out_write(leds_val);
    }
}
