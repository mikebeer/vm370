#!/bin/bash
# M5e: the cREXX 2022 S370 tree (commit d042dcc6d, F0041, 12 Jun 2022 --
# the last commit where S370/cmsmake.exec matches its sources) as one
# card deck for CMSUSER: ID card, then ':READ  FN FT D1' per file, so
# READCARD * unpacks it onto the D disk.
#  - re2c 2.1.1 / lemon are built on the host from the same commit and
#    run exactly as S370/cmslocalbuild.sh does (the EBCDIC encoding.re).
#  - the reader is F 80: tabs are expanded, and C/H lines over 80 columns
#    are split at column 79 with a backslash-newline -- translation phase 2
#    splices them back before tokenisation, string literals included.
#  - CMSMAKE EXEC is replaced by CRXMAKE EXEC (compiles via GCC31 = GCC380,
#    AMODE 31, heap above 16 MB; builds RXBVM, 'Out of memory' on CE).
# Steps used on 6 October are in docs/36-M5-CMS31.md (M5e).
