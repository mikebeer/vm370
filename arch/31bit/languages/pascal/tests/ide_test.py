#!/usr/bin/env python3
"""Unit tests for the editor core of the Turbo-Pascal-style environment (no terminal needed)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'ide'))
import tpide

e = tpide.Editor()
e.lines = ["begin", "  x:=1;", "end."]
e.cy, e.cx = 1, 8
e.newline(); e.insert_char('y')
assert e.lines[2] == "  y", e.lines            # auto indent
e.do_undo(); e.do_undo()
assert e.lines == ["begin", "  x:=1;", "end."], e.lines
e.mark_b, e.mark_k = (0, 0), (1, 3)
assert e.block_text() == ["begin", "  x"]
e.cy, e.cx = 2, 0
e.insert_text(e.block_text())
assert e.lines[3] == "  xend.", e.lines
assert e.find("END")[0] == 3
e.delete_line(); assert len(e.lines) == 3
spans, c = tpide.classify_line("x := 'a'; {c} begin (* z", None)
assert (14, 19, 'k') in spans and c == '*)'
print("ide tests passed")
