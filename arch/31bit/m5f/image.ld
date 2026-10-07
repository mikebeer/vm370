OUTPUT_FORMAT(elf32-s390)
OUTPUT_ARCH(s390:31-bit)
ENTRY(cms_entry)
SECTIONS
{
  . = 0;
  .text : { KEEP(*(.text.entry)) *(.text .text.*) }
  .rodata : ALIGN(8) { *(.rodata .rodata.*) }
  .data : ALIGN(8) { *(.data .data.*) }
  .bss : ALIGN(8) { *(.bss .bss.*) *(COMMON) }
  /DISCARD/ : { *(.note.GNU-stack) *(.comment) *(.eh_frame) }
}
