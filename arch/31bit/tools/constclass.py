#!/usr/bin/env python3
"""
Classify every use of PSA.MACRO's architecture-dependent constants.

08-MACRO-UNDERCOUNT.md found six constants with 217 reference sites and noted
the catch: widening a mask is only correct where the old width was incidental.
A site doing N R1,XRIGHT24 to CLEAR FLAGS wants the narrow mask to keep
working; one doing it to TRUNCATE AN ADDRESS wants the wide one. This sorts
them.

    python3 constclass.py /path/to/source/cp            # summary
    python3 constclass.py /path/to/source/cp XRIGHT16   # every site, one name

METHOD, AND WHY IT IS TRUSTWORTHY HERE.  Two signals, used together:

  1. The INSTRUCTION FORM, which is mechanical.  N/NC mask, O/OC set, ICM
     inserts selected bytes, C/CL compare, L loads the value for later use.
  2. The COMMENT.  CP is commented at nearly every line and the comments state
     intent -- "BLANK HIGH BYTE", "ISOLATE ENDING PAGE NO.", "GET THE TIMEOUT
     COUNT".  That is what distinguishes a count from an address, and no
     amount of instruction analysis would.

Only operand-field matches count.  An earlier pass matched the comment field
too and produced impossible readings like STCTL storing into a constant.
"""
import collections
import glob
import re
import sys
from pathlib import Path

CONSTS = {
    "CPCREG0":  "X'81800CC0'",
    "XPAGNUM":  "X'00FFF000'",
    "XRIGHT16": "X'0000FFFF'",
    "X2048BND": "X'00FFF800'",
    "XRIGHT24": "X'00FFFFFF'",
    "X40FFS":   "X'40FFFFFF'",
    "NOADD":    "X'FF000000'",
}

# Comment words that identify what the masked value actually IS. A quantity
# that is 16 bits because it counts something stays 16 bits; one that is
# 16 or 24 bits because an address used to fit does not.
ADDRESSY = re.compile(r"\b(ADDRESS|ADDR|PAGE +NO|PAGE +NUM|SEG |SEGMENT|"
                      r"BOUND|CORE|FRAME|LOCATION)", re.I)
QUANTITY = re.compile(r"\b(COUNT|CODE|NUMBER|MSG|MESSAGE|FLAG|TIMEOUT|"
                      r"BYTE.COUNT|LENGTH|MASK ALL|ERROR)", re.I)


def statements(path):
    for n, raw in enumerate(open(path, encoding="utf-8", errors="replace"), 1):
        line = raw.rstrip("\n")[:71]
        if not line.strip() or line[:1] in ("*", "."):
            continue
        f = line.split()
        if line[:1].isspace():
            op, rest = f[0].upper(), f[1:]
        else:
            if len(f) < 2:
                continue
            op, rest = f[1].upper(), f[2:]
        if not rest:
            continue
        # Strip CP's change markers, which are not comment text.
        comment = re.sub(r"[@%$]V?[A-Z0-9]+\s*$", "",
                         " ".join(rest[1:])).strip()
        yield n, op, rest[0], comment


def collect(root):
    out = collections.defaultdict(list)
    for f in sorted(glob.glob(str(Path(root) / "*.ASSEMBLE"))):
        mod = Path(f).stem
        for n, op, operand, comment in statements(f):
            for c in CONSTS:
                if re.search(r"\b" + c + r"\b", operand):
                    out[c].append((mod, n, op, comment))
    return out


def verdict(const, op, comment):
    """Which of the four classes does this site fall into?"""
    if const == "CPCREG0":
        # Not a mask at all: STCTL saves the live CR0 here and LCTL reloads it.
        return "A", "CR0 save/restore -- follows the definition"
    if const in ("X40FFS", "NOADD"):
        # A flag living in bits 0-7, which become address bits.
        return "D", "flag in bits 0-7 -- must relocate, not widen"
    if const == "XRIGHT16":
        if ADDRESSY.search(comment) and not QUANTITY.search(comment):
            return "C-break", "16 bits cannot hold this any more"
        return "C-safe", "genuine 16-bit quantity"
    return "B", "widen the definition"


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    only = sys.argv[2].upper() if len(sys.argv) > 2 else None
    sites = collect(root)

    if only:
        print(f"{only}  {CONSTS.get(only,'')}   {len(sites[only])} sites\n")
        for mod, n, op, comment in sites[only]:
            cls, why = verdict(only, op, comment)
            print(f"  {cls:8} {mod:9} {n:>5}  {op:5} {comment[:44]}")
        return

    print(f"{'constant':10} {'value':13} {'refs':>5}  class  action")
    print("-" * 78)
    totals = collections.Counter()
    for c, val in CONSTS.items():
        cls = collections.Counter()
        for mod, n, op, comment in sites[c]:
            k, why = verdict(c, op, comment)
            cls[k] += 1
            totals[k] += 1
        for k, v in cls.most_common():
            _, why = verdict(c, "", "ADDRESS" if k == "C-break" else "COUNT")
            print(f"{c:10} {val:13} {v:>5}  {k:7} {why}")
    print("-" * 78)
    print(f"{'':10} {'':13} {sum(totals.values()):>5}  total\n")
    print("A       one definition change, every site follows          "
          f"{totals['A']:>4}")
    print("B       widen the definition, every site follows           "
          f"{totals['B']:>4}")
    print("C-safe  leave alone -- a genuine 16-bit quantity           "
          f"{totals['C-safe']:>4}")
    print("C-break 16 bits no longer holds it -- per-site fix         "
          f"{totals['C-break']:>4}")
    print("D       a flag in bits 0-7 -- relocate it, design decision "
          f"{totals['D']:>4}")
    print(f"\nNeeding individual attention: "
          f"{totals['C-break'] + totals['D']} of {sum(totals.values())}. "
          f"Four definition changes carry the other "
          f"{totals['A'] + totals['B'] + totals['C-safe']}.")


if __name__ == "__main__":
    main()
