INCLUDE output_format.ld
ENTRY(_start)

__DYNAMIC = 0;

INCLUDE regions.ld


SECTIONS
{
	.text :
	{
		_ftext = .;
		*(SORT(.text.start))
		*(SORT(.text))
		*(SORT(.stub))
		*(SORT(.text.*))
		*(SORT(.gnu.linkonce.t.*))
		_etext = .;
	} > rom

	.rodata :
	{
		/*
		 * Align models and large chunks of data into a constant position
		 */
		. = _ftext + 0x98000;
		_frodata = .;
		src/models/*/*(SORT(.rodata.*))
		src/conv2d_??.o(SORT(.rodata.*))  /* specific to hps_accel */
		. = ALIGN(4096);
		*(SORT(.rodata))
		*(SORT(.rodata.*))
		*(SORT(.gnu.linkonce.r.*))
		*(SORT(.rodata1))
		*(SORT(.srodata))
		*(SORT(.srodata.*))
		. = ALIGN(8);
		_erodata = .;
	} > rom

	.data : AT (ADDR(.rodata) + SIZEOF (.rodata))
	{
		. = ALIGN(8);
		_fdata = .;
		*(SORT(.data))
		*(SORT(.data.*))
		*(SORT(.gnu.linkonce.d.*))
		*(SORT(.data1))
		*(SORT(.ramtext))
		*(SORT(.ramtext.*))
		_gp = ALIGN(16);
		*(SORT(.sdata))
		*(SORT(.sdata.*))
		*(SORT(.gnu.linkonce.s.*))
		*(SORT(.sdata2))
		*(SORT(.sdata2.*))
		_edata = ALIGN(16); /* Make sure _edata is >= _gp. */
	} > sram

	.bss : AT (ADDR(.data) + SIZEOF (.data))
	{
		. = ALIGN(16);
		_fbss = .;
		*(SORT(.dynsbss))
		*(SORT(.sbss))
		*(SORT(.sbss.*))
		*(SORT(.gnu.linkonce.sb.*))
		*(SORT(.scommon))
		*(SORT(.dynbss))
		*(SORT(.bss))
		*(SORT(.bss.*))
		*(SORT(.gnu.linkonce.b.*))
		*(SORT(COMMON))
		. = ALIGN(8);
		_ebss = .;
		_end = .;
	} > sram

        .arena (NOLOAD) :
        {
                _farena = .;
                *(.arena)
                _earena = .;
        } > arena
}

PROVIDE(_fstack = ORIGIN(sram) + LENGTH(sram) - 4);
