#!/usr/bin/env python3
"""
A two-pass assembler for the DAT test programs, just big enough for them.

Written after step 3 failed on a stale high byte in the base register: the
fix was one extra instruction, which shifted every displacement, and
hardcoded addresses made that a transcription exercise instead of an edit.

Labels on aligned data are assigned AFTER the padding, not before -- doing
it the other way round was this file's own first bug, caught by
check_align rather than by a Hercules run, which is the point of having
the check.
"""

class Asm:
    def __init__(self, origin=0x2000):
        self.origin = origin
        self.items = []
        self.labels = {}
        self.base = None          # the address the USING assumes

    # --------------------------------------------------------- building
    def label(self, name):
        self.items.append(("label", name))

    def align(self, n, fill=b"\x07\x00"):
        self.items.append(("align", n, fill))

    def insn(self, length, build, src, note=""):
        """build(asm) -> bytes, called in pass two once labels are known."""
        self.items.append(("insn", length, build, src, note))

    def data(self, name, build, note="", align=1, size=None):
        """Aligned datum. The label lands after the padding.

        `size` is needed when build() forward-references a label placed
        later: the layout pass cannot call the builder then, because the
        label it wants does not exist yet.  Declared size is checked
        against what pass two actually produces.
        """
        self.items.append(("data", name, build, note, align, size))

    # --------------------------------------------------- pass one, sizes
    def layout(self):
        a = self.origin
        for it in self.items:
            k = it[0]
            if k == "label":
                self.labels[it[1]] = a
            elif k == "align":
                while a % it[1]:
                    a += len(it[2])
            elif k == "insn":
                a += it[1]
            elif k == "data":
                n = it[4]
                while a % n:
                    a += 1
                self.labels[it[1]] = a       # after the padding
                a += it[5] if it[5] is not None else len(it[2](self))
        self.end = a
        return self

    # --------------------------------------------------------- operands
    def bd(self, r, name, off=0):
        """Base-displacement operand, checked against the 12-bit field."""
        target = self.labels[name] + off
        d = target - self.base
        if not 0 <= d <= 0xFFF:
            raise SystemExit("%s (%06X) out of reach of base %06X: disp %X"
                             % (name, target, self.base, d))
        return bytes([(r << 4) | (d >> 8), d & 0xFF])

    def addr(self, name):
        return self.labels[name]

    # --------------------------------------------------- pass two, bytes
    def assemble(self, size=0x1080):
        img = bytearray(size)
        listing = []
        a = self.origin
        for it in self.items:
            k = it[0]
            if k == "label":
                continue
            if k == "align":
                n, fill = it[1], it[2]
                while a % n:
                    img[a-self.origin:a-self.origin+len(fill)] = fill
                    listing.append((a, fill, "(align)", ""))
                    a += len(fill)
                continue
            if k == "insn":
                length, build, src, note = it[1], it[2], it[3], it[4]
                raw = build(self)
                if len(raw) != length:
                    raise SystemExit("%s: declared %d bytes, built %d"
                                     % (src, length, len(raw)))
            else:
                name, build, note, n, declared = it[1], it[2], it[3], it[4], it[5]
                while a % n:
                    a += 1
                raw, src = build(self), name
                if declared is not None and len(raw) != declared:
                    raise SystemExit("%s: declared %d bytes, built %d"
                                     % (name, declared, len(raw)))
            img[a-self.origin:a-self.origin+len(raw)] = raw
            listing.append((a, raw, src, note))
            a += len(raw)
        if a != self.end:
            raise SystemExit("layout %06X but assembled to %06X" % (self.end, a))
        self.img, self.listing = img, listing
        return self

    def put(self, addr, raw):
        # Bounds-checked deliberately.  bytearray slice assignment APPENDS
        # when the start is past the end instead of failing, so an address
        # outside the image silently lands on the tail and the pokes come
        # out wrong with nothing to show for it.  This bit once already.
        lo = addr - self.origin
        if lo < 0 or lo + len(raw) > len(self.img):
            raise SystemExit(
                "put(%06X, %d bytes) outside the image %06X-%06X: "
                "grow it with assemble(size=...)"
                % (addr, len(raw), self.origin, self.origin + len(self.img) - 1))
        self.img[lo:lo+len(raw)] = raw

    def read(self, addr, n):
        lo = addr - self.origin
        if lo < 0 or lo + n > len(self.img):
            raise SystemExit("read(%06X) outside the image" % addr)
        return bytes(self.img[lo:lo+n])

    # --------------------------------------------------------- checking
    def check_align(self, *specs):
        for name, n, why in specs:
            if self.labels[name] % n:
                raise SystemExit("%s at %06X misaligned for %s (needs %d)"
                                 % (name, self.labels[name], why, n))

    def print_listing(self):
        for addr, raw, src, note in self.listing:
            print("  %06X  %-12s %-24s %s"
                  % (addr, raw.hex().upper(), src, ("* " + note) if note else ""))

    def pokes(self, *ranges):
        out = []
        for start, end, step in ranges:
            for x in range(start, end, step):
                n = min(step, end - x)
                out.append("r %04X=%s" % (x, self.read(x, n).hex().upper()))
        return out


def psw(ia):
    """A disabled-wait PSW: bit 12 on as ESA/390 requires, bit 14 for wait."""
    return bytes.fromhex("000A0000") + ia.to_bytes(4, "big")
