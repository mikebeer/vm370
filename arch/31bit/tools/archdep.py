#!/usr/bin/env python3
"""
Measure the architecture-dependent surface of a set of CP modules.

Used to scope M1 -- CP IPLing in ESA/390 mode and writing one console
message -- against the whole of CP, so the first milestone is a work list
rather than a description.

    python3 archdep.py /path/to/source/cp            # everything
    python3 archdep.py /path/to/source/cp DMKCPI ...  # a named subset

Method, and its known limit.  Comment lines (* and .) are skipped; columns
beyond 71 are ignored because 72 is the continuation column; the opcode is
the first blank-delimited field when column 1 is blank and the second
otherwise.  IT CANNOT SEE MACRO-GENERATED INSTRUCTIONS, so every count is a
FLOOR.  Macro invocations are counted separately for exactly that reason --
TRANS alone hides an LCTL, an LRA and a conditional branch per site.
"""
import re
import sys
from collections import Counter
from pathlib import Path

# S/370 I/O instructions, all removed by the channel subsystem.
IO_370 = {"SIO", "SIOF", "TIO", "HDV", "HIO", "TCH", "CLRIO", "CLRCH",
          "STIDC", "RIO", "RRB"}
# Instructions whose behaviour or operands change under ESA/390.
ARCH = {"LCTL", "STCTL", "LPSW", "SSM", "LRA", "ISK", "SSK", "IVSK",
        "PTLB", "STNSM", "STOSM", "SPKA", "SPX", "STPX", "SIGP", "STIDP",
        "BSM", "BASSM", "IPTE", "TPROT", "SPX", "DIAG"}
# CP macros that hide architecture-dependent instructions.
MACROS = {"TRANS", "CALL", "RETURN", "GOTO", "SAVE", "VMFREE", "LOCK",
          "UNLOCK", "SWTCHVM", "TRANRET"}
# Fields whose width or position changes with the DAT format.
DATFIELDS = {"SEGPAGE", "SEGPLEN", "SEGINV", "SEGMIG", "SEGENQ",
             "PAGCORE", "PAGINVAL", "PAGREF", "PAGTSWP", "PAGBMP",
             "SWPKEY1", "SWPKEY2", "SWPREF1", "SWPCHG1", "SWPREF2",
             "SWPCHG2", "VMSEG"}
CAWCSW = {"CSW", "CAW", "IOBCSW", "IOBCAW", "VDEVCSW", "VDEVCAW"}


def statements(path):
    """Yield (opcode, operand_text) for real statements only."""
    with open(path, encoding="utf-8", errors="replace") as fh:
        for raw in fh:
            line = raw.rstrip("\n")[:71]
            if not line.strip() or line[:1] in ("*", "."):
                continue
            fields = line.split()
            if line[:1].isspace():
                op = fields[0]
                rest = fields[1:]
            else:
                if len(fields) < 2:
                    continue
                op = fields[1]
                rest = fields[2:]
            yield op.upper(), " ".join(rest)


def measure(path):
    c = Counter()
    text = open(path, encoding="utf-8", errors="replace").read()
    body = "\n".join(l[:71] for l in text.split("\n")
                     if l[:1] not in ("*", "."))
    for op, operand in statements(path):
        if op in IO_370:
            c["io370"] += 1
            c["io:" + op] += 1
        if op in ARCH:
            c["arch"] += 1
            c["arch:" + op] += 1
        if op in MACROS:
            c["macro"] += 1
            c["macro:" + op] += 1
    for f in DATFIELDS:
        n = len(re.findall(r"\b" + f + r"\b", body))
        if n:
            c["dat"] += n
            c["dat:" + f] += n
    for f in CAWCSW:
        n = len(re.findall(r"\b" + f + r"\b", body))
        if n:
            c["cawcsw"] += n
    c["lines"] = body.count("\n")
    return c


def main():
    root = Path(sys.argv[1])
    names = sys.argv[2:]
    if names:
        files = [root / (n if n.endswith(".ASSEMBLE") else n + ".ASSEMBLE")
                 for n in names]
    else:
        files = sorted(root.glob("*.ASSEMBLE"))
    files = [f for f in files if f.exists()]

    total = Counter()
    rows = []
    for f in files:
        c = measure(f)
        total.update(c)
        rows.append((f.stem, c))

    rows.sort(key=lambda r: -(r[1]["io370"] + r[1]["arch"] + r[1]["dat"]))

    print(f"{'module':10} {'lines':>6} {'S/370 I/O':>9} {'arch':>6} "
          f"{'DAT':>5} {'CAW/CSW':>8} {'macros':>7}")
    print("-" * 60)
    for name, c in rows:
        if not (c["io370"] or c["arch"] or c["dat"] or c["cawcsw"]):
            continue
        print(f"{name:10} {c['lines']:>6} {c['io370']:>9} {c['arch']:>6} "
              f"{c['dat']:>5} {c['cawcsw']:>8} {c['macro']:>7}")
    print("-" * 60)
    print(f"{'TOTAL':10} {total['lines']:>6} {total['io370']:>9} "
          f"{total['arch']:>6} {total['dat']:>5} {total['cawcsw']:>8} "
          f"{total['macro']:>7}")
    print(f"\n{len(files)} modules examined"
          f"{' (subset)' if names else ''}")

    print("\nS/370 I/O instructions by mnemonic:")
    for k in sorted(k for k in total if k.startswith("io:")):
        print(f"    {k[3:]:8} {total[k]}")
    print("\nArchitecture-sensitive instructions:")
    for k in sorted(total, key=lambda k: -total[k]):
        if k.startswith("arch:"):
            print(f"    {k[5:]:8} {total[k]}")
    print("\nMacro invocations -- each may hide more than one instruction:")
    for k in sorted(total, key=lambda k: -total[k]):
        if k.startswith("macro:"):
            print(f"    {k[6:]:8} {total[k]}")


if __name__ == "__main__":
    main()
