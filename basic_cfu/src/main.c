#include <generated/csr.h>
#include <hw/common.h>
#include <console.h>
#include <stdio.h>
#include <irq.h>
#include <uart.h>

#include "cfu.h"
#include "perf.h"
#include "riscv.h"

#define NEWASM

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

#ifdef NEWASM
        //   r = opcode_R(opcode, funct3, funct7, s1, s2)
        int r0 = opcode_R(CUSTOM0, 0, 0, v0, v1);       // byte sum
        int r1 = opcode_R(CUSTOM0, 1, 0, v0, v1);       // byte swap
        int r2 = opcode_R(CUSTOM0, 2, 0, v0, v1);       // bit reverse
#else
        int r0 = RunCustomInstruction0(v0, v1);       // byte sum
        int r1 = RunCustomInstruction1(v0, v1);       // byte swap
        int r2 = RunCustomInstruction2(v0, v1);       // bit reverse
#endif
        puts("arg0        arg1        bytesum     byteswap    bitrev");
        printf("0x%08x, 0x%08x: 0x%08x, 0x%08x, 0x%08x\n", v0, v1, r0, r1, r2);
        printf("  %08d,   %08d:   %08d,   %08d,   %08d\n", v0, v1, r0, r1, r2);
        puts("\n");
}

void __attribute__ ((noinline)) run_cfu()
{
        puts("\n\nCFU TEST:");
        puts("arg0        arg1        bytesum     byteswap    bitrev");
        for (int i=0; i<0x50505; i+=0x8103) {
#ifdef NEWASM
            //   r = opcode_R(opcode, funct3, funct7, s1, s2)
            int v0 = opcode_R(CUSTOM0, 0, 0, i, i);       // byte sum
            int v1 = opcode_R(CUSTOM0, 1, 0, i, i);       // byte swap
            int v2 = opcode_R(CUSTOM0, 2, 0, i, i);       // bit reverse
#else
            int v0 = RunCustomInstruction0(i, i);       // byte sum
            int v1 = RunCustomInstruction1(i, i);       // byte swap
            int v2 = RunCustomInstruction2(i, i);       // bit reverse
#endif
            printf("0x%08x, 0x%08x: 0x%08x, 0x%08x, 0x%08x\n", i, i, v0, v1, v2);
        }
        puts("\n");
}


int main(void) 
{
    leds_out_write(0xf);
    int leds_val = 0x0;


    irq_setmask(0);
    irq_setie(1);
    uart_init();

    puts("Press the following keys to test CFU functions:\n"
        "c - Test instructions 0-2 with various inputs\n"
        "d - Test instructions on user supplied inputs\n"
        "z - Zero cycle timer\n"
        "m - Print current timer value\n"
        "e - Enable perf counter\n"
        "0 - Select perf counter 0\n"
        "1 - Select perf counter 1\n"
        "p - Pause perf counter\n");

    
    int counter_num = 0;
    while (1) {
        char c = readchar();
        putchar(c);
        // double up if odd
        if (c & 0x1 && c != '1') putchar(c);
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
            printf("\nzero-out mcycle and counter %d\n", counter_num);
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
        leds_val += 1;
        leds_out_write(leds_val);
    }
}
