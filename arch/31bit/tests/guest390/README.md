# guest390 — ESA/390 test guests for M7 (docs/39-M7-ESA-GUESTS.md)

Each `gNNN.s` is a stand-alone program IPLed from tape at X'400' in ESA/390
format, results at X'1000' (16 bytes per test: tag, info, 8 bytes data;
info `CCxx000c` = ran with condition code c, else the program interruption
ILC+code from X'8C').

    s390x-linux-gnu-as -m31 -mesa -o g390a.o g390a.s
    s390x-linux-gnu-objcopy -O binary -j .text g390a.o g390a.bin
    python3 mkg390.py g390a.bin ../../../../scratchpad/VM370CE.V1.R1.2/io/g390a.aws

Run: `../runs/g390a.json` (MAINT, `ATTACH 480 AS 181`, `IPL 181`, `D 1000.80`).

| Program | Increment | What it records |
|---|---|---|
| g390a | M7.0 | lowcore X'00'/X'B8' after IPL; STIDP, STSCH, TPI, STAP, SSCH |
