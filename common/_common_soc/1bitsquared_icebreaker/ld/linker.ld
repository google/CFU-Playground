INCLUDE output_format.ld
ENTRY(_start)

__DYNAMIC = 0;

INCLUDE regions.ld


SECTIONS
{
    /* .data first to take precedence for explicit code we want in SRAM. */
    .data : AT (_erodata) /* Loaded in spiflash but runtime copied to SRAM. */
    {
        . = ALIGN(4);
        _fdata = .;  /* Start of .data in SRAM, copied to in crt0. */

        *(.ramtext .ramtext*)

        /* 
         * We need to ensure .data starts at > 0, otherwise a pointer to the
         * first element of .data will be mistaken for a nullptr.
         */
        . = MAX(., 0x4); 

        *(.data .data*)
        *(.sdata .sdata*)

        . = ALIGN(4);
        _edata = .;  /* End of .data in SRAM, end of copying in crt0. */
    } > sram

    /* Start .text at 4 byte boundary after gateware. */
    _ftext = (ORIGIN(spiflash) + 0x30000 + 3) & ~3;
    .text _ftext :
    {
        *(.text.start)
        *(.text .text*)
    } > spiflash

    .rodata :
    {
        *(.rodata .rodata*)
        *(.srodata .srodata*)

        . = ALIGN(4);
        _erodata = .;  /* Start of .data in spiflash, copied from in crt0. */
    } > spiflash

    .bss :
    {
        . = ALIGN(4);
        _fbss = .;  /* Start of zeroing in crt0. */

        *(.bss .bss*)
        *(.sbss .sbss*)

        *(COMMON)
        
        . = ALIGN(4);
        _ebss = .;  /* End of zeroing in crt0. */
    } > sram
}

PROVIDE(_fstack = ORIGIN(sram) + LENGTH(sram) - 4);
