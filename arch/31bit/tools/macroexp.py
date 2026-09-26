#!/usr/bin/env python3
"""
How bad is the macro undercount?

Every instruction count in 03-CP-INVENTORY.md and 07-M1-WORKLIST.md is a
FLOOR, because a statement parser cannot see what a macro emits.  TRANS was
found by accident and hides an LCTL, an LRA and a branch at each of 174
sites; CALL hides 4,104 linkages.  Nobody has established what else is
hidden, and that is the largest unquantified risk in the whole inventory.

This answers it.  For every .MACRO member it extracts the instructions the
body can emit, resolves nested macro calls transitively (SWTCHVM calls
CHARGE, so its cost is not local), and then multiplies each module's macro
invocations by what those macros carry.

    python3 macroexp.py /path/to/source/cp

WHAT THE NUMBERS MEAN, AND DO NOT MEAN.  Macro bodies are full of
conditional assembly -- AIF, AGO, SETB -- so not every instruction in a body
is emitted at every invocation.  What this computes is therefore an UPPER
BOUND per invocation, which is the right quantity for a risk assessment:
it says how much could be hidden, not how much is.  The floor from the
statement parser and the ceiling from here bracket the real figure.

DC IS TREATED AS A POSSIBLE INSTRUCTION.  CP hand-encodes instructions its
assembler does not know -- DMKVATZP DC X'E60B',S(ARCHTECT,0(R9)) is an
ECPS:VM assist -- so a DC whose first operand is a 2- or 4-byte hex literal
is reported separately rather than ignored.  That is exactly the idiom
XAOPS.MACRO uses, so the same blindness would apply to converted code.
"""
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

IO_370 = {"SIO", "SIOF", "TIO", "HDV", "HIO", "TCH", "CLRIO", "CLRCH",
          "STIDC", "RIO"}
ARCH = {"LCTL", "STCTL", "LPSW", "SSM", "LRA", "ISK", "SSK", "IVSK",
        "PTLB", "RRB", "STNSM", "STOSM", "SPKA", "SPX", "STPX", "SIGP",
        "STIDP", "BSM", "BASSM", "IPTE", "TPROT", "DIAG"}

# Conditional assembly, listing control and symbol definition: emit nothing.
DIRECTIVES = {
    "MACRO", "MEND", "MEXIT", "MNOTE", "AIF", "AGO", "ANOP", "ACTR",
    "SETA", "SETB", "SETC", "GBLA", "GBLB", "GBLC", "LCLA", "LCLB", "LCLC",
    "AREAD", "COPY", "SPACE", "EJECT", "TITLE", "PRINT", "PUSH", "POP",
    "ISEQ", "USING", "DROP", "CSECT", "DSECT", "START", "END", "ORG",
    "LTORG", "EXTRN", "ENTRY", "WXTRN", "AMODE", "RMODE", "EQU", "DS",
    "CNOP", "REPRO", "PUNCH", "OPSYN", "ICTL",
}


def body_statements(path):
    """Yield (opcode, operand) from a macro body, skipping comments.
    A '.' in column 1 is a conditional-assembly comment or sequence
    symbol; '*' is an ordinary comment."""
    for raw in open(path, encoding="utf-8", errors="replace"):
        line = raw.rstrip("\n")[:71]
        if not line.strip() or line[:1] == "*":
            continue
        fields = line.split()
        if line[:1].isspace():
            op, rest = fields[0], fields[1:]
        else:
            # A label, or a sequence symbol like .NOLABEL -- either way the
            # opcode is the second field if there is one.
            if len(fields) < 2:
                continue
            op, rest = fields[1], fields[2:]
        yield op.upper(), " ".join(rest)


def analyse_macro(path):
    """What can this macro body emit, locally?"""
    out = {"arch": Counter(), "io": Counter(), "calls": set(), "dc": 0}
    for op, operand in body_statements(path):
        if op in DIRECTIVES:
            continue
        if op == "DC":
            # A hand-encoded instruction looks like  DC X'B233',S(...)
            if re.match(r"^X'[0-9A-Fa-f]{4,8}'", operand):
                out["dc"] += 1
            continue
        if op in ARCH:
            out["arch"][op] += 1
        elif op in IO_370:
            out["io"][op] += 1
        else:
            out["calls"].add(op)          # may be a nested macro
    return out


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    macros = {p.stem: p for p in root.glob("*.MACRO")}
    local = {name: analyse_macro(p) for name, p in macros.items()}

    # Keep only nested calls that are really macros in this library.
    for name, info in local.items():
        info["calls"] = {c for c in info["calls"] if c in macros and c != name}

    # Transitive closure over nesting.
    def total_for(name, seen=None):
        seen = seen or set()
        if name in seen:
            return Counter(), Counter(), 0
        seen = seen | {name}
        a = Counter(local[name]["arch"])
        i = Counter(local[name]["io"])
        d = local[name]["dc"]
        for callee in local[name]["calls"]:
            ca, ci, cd = total_for(callee, seen)
            a.update(ca)
            i.update(ci)
            d += cd
        return a, i, d

    totals = {n: total_for(n) for n in macros}

    print(f"{'macro':12} {'arch insns hidden':32} {'S/370 I/O':12} "
          f"{'DC':>3} nests")
    print("-" * 78)
    interesting = []
    for name in sorted(macros):
        a, i, d = totals[name]
        if not (a or i or d):
            continue
        interesting.append(name)
        arch_s = " ".join(f"{k}x{v}" for k, v in sorted(a.items()))
        io_s = " ".join(f"{k}x{v}" for k, v in sorted(i.items()))
        nests = ",".join(sorted(local[name]["calls"])) or "-"
        print(f"{name:12} {arch_s[:32]:32} {io_s[:12]:12} {d:>3} {nests}")
    print("-" * 78)
    print(f"{len(macros)} macros; {len(interesting)} can emit something "
          f"architecture-dependent")
    clean = sorted(set(macros) - set(interesting))
    print(f"\nEmit nothing architecture-dependent ({len(clean)}):")
    print("   " + " ".join(clean))

    # Now weight by how often each is invoked across CP.
    print("\n" + "=" * 78)
    print("WEIGHTED BY INVOCATION COUNT ACROSS CP")
    print("=" * 78)
    invocations = Counter()
    for src in sorted(root.glob("*.ASSEMBLE")):
        for op, _ in body_statements(src):
            if op in macros:
                invocations[op] += 1

    grand_a, grand_i, grand_d = Counter(), Counter(), 0
    print(f"{'macro':12} {'sites':>6} {'hidden arch insns':>18} "
          f"{'hidden I/O':>11} {'hidden DC':>10}")
    print("-" * 62)
    for name, n in invocations.most_common():
        a, i, d = totals[name]
        na, ni, nd = sum(a.values()) * n, sum(i.values()) * n, d * n
        if not (na or ni or nd):
            continue
        grand_a.update({k: v * n for k, v in a.items()})
        grand_i.update({k: v * n for k, v in i.items()})
        grand_d += nd
        print(f"{name:12} {n:>6} {na:>18} {ni:>11} {nd:>10}")
    print("-" * 62)
    print(f"{'CEILING':12} {'':>6} {sum(grand_a.values()):>18} "
          f"{sum(grand_i.values()):>11} {grand_d:>10}")
    if grand_a:
        print("\nHidden architecture-sensitive instructions, by mnemonic:")
        for k, v in grand_a.most_common():
            print(f"    {k:8} {v}")
    if grand_i:
        print("\nHidden S/370 I/O instructions, by mnemonic:")
        for k, v in grand_i.most_common():
            print(f"    {k:8} {v}")

    print("\nMacros never invoked in .ASSEMBLE members "
          "(DSECT/table generators, or dead):")
    never = sorted(set(macros) - set(invocations))
    print("   " + " ".join(never))


if __name__ == "__main__":
    main()
