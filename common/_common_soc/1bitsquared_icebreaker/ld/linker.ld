INCLUDE output_format.ld
ENTRY(_start)

__DYNAMIC = 0;

INCLUDE regions.ld


SECTIONS
{
	.reserved :
	{
		/* Space reserved for gateware, shouldn't step on it. */
		. += 0x30000;
	} > spiflash

	.text :
	{
		_ftext = .;
		*(.text.start)
		*(.text .stub .text.* .gnu.linkonce.t.*)
		_etext = .;
	} > spiflash

	.rodata :
	{
		. = ALIGN(8);
		_frodata = .;
		*(.rodata .rodata.* .gnu.linkonce.r.*)
		*(.rodata1)
		*(.srodata .srodata.*)
		. = ALIGN(8);
		_erodata = .;
	} > spiflash

	.data : AT (ADDR(.rodata) + SIZEOF (.rodata))
	{
		. = ALIGN(8);
		_fdata = .;
		*(.data .data.* .gnu.linkonce.d.*)
		*(.data1)
		*(.ramtext .ramtext.*)
		_gp = ALIGN(16);
		*(.sdata .sdata.* .gnu.linkonce.s.* .sdata2 .sdata2.*)
		_edata = ALIGN(16); /* Make sure _edata is >= _gp. */
	} > sram

	.bss : AT (ADDR(.data) + SIZEOF (.data))
	{
		. = ALIGN(16);
		_fbss = .;
		*(.dynsbss)
		*(.sbss .sbss.* .gnu.linkonce.sb.*)
		*(.scommon)
		*(.dynbss)
		*(.bss .bss.* .gnu.linkonce.b.*)
		*(COMMON)
		. = ALIGN(8);
		_ebss = .;
		_end = .;
	} > sram
}

PROVIDE(_fstack = ORIGIN(sram) + LENGTH(sram) - 4);
