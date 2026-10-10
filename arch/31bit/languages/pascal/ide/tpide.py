#!/usr/bin/env python3
"""Turbo-Pascal-style integrated environment for the cREXX Pascal compiler.

A full-screen text editor with a menu bar, block commands, search and replace,
syntax colouring, one-key compile / run, an error message window that jumps to
the offending line, and a help window.  It drives the compiler in this
repository (pascal.rxbin + pasrt.rxbin) through the cREXX tools rxvm and rxas.
"""
import curses, os, re, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

KEYWORDS = set("""and array begin case const div do downto else end file for function goto if in
label mod nil not of or packed procedure program record repeat set then to type until var while
with forward""".split())
BUILTIN = set("""integer real boolean char string true false write writeln read readln abs sqr sqrt sin cos
arctan ln exp trunc round odd ord chr succ pred new dispose length copy pos concat upcase eof eoln
maxint""".split())

SKELETON = "program Noname;\nbegin\n  writeln('Hello, world!')\nend.\n"

HELP = """
 Turbo Pascal for cREXX -- quick reference
 -----------------------------------------
 Keys
   F1 Help          F2 Save           F3 Open          F9 Make (compile)
   Ctrl-R / Ctrl-F9 Run               F10 Menu         Alt-X Exit
   Alt-F/E/S/R/C/O/H  open a menu     Ctrl-Z Undo      Ctrl-Y Delete line
   Ctrl-K B / K   mark block begin / end       Ctrl-K C / V / Y  copy / move / delete block
   Ctrl-K R / W   read block from / write block to a file
   Ctrl-Q F  Find        Ctrl-Q A  Replace        Ctrl-L  Search again
   Ctrl-Q G  Go to line  Ctrl-T  Delete word      Ins  Insert / Overwrite

 Language supported by the compiler
   integer real boolean char string, subranges, enumerations, arrays,
   records, pointers (new / dispose), const / type / var,
   procedures and functions (nested, recursive, var parameters, forward),
   if while repeat for case with, write / writeln / read / readln
   with field widths, and the usual standard functions.
   Not yet: sets, files, variant records, goto, procedural parameters.

 Program layout
   program Name;
   const ...  type ...  var ...
   procedure / function declarations
   begin
     statements
   end.

 When the compiler finds an error the Messages window opens and the cursor
 jumps to the line.  Press F9 again after fixing it.  Esc closes a window.
"""

def classify_line(line, incomment):
    """Return (list of (start, end, kind)), incomment_after.  kinds: k keyword, c comment,
    s string, n number, b builtin"""
    out = []
    i, n = 0, len(line)
    while i < n:
        if incomment:
            j = line.find(incomment if incomment == '}' else '*)', i)
            if j < 0:
                out.append((i, n, 'c')); return out, incomment
            j += 1 if incomment == '}' else 2
            out.append((i, j, 'c')); i = j; incomment = None; continue
        ch = line[i]
        if ch == '{':
            incomment = '}'; out.append((i, i + 1, 'c')); i += 1
            j = line.find('}', i)
            if j >= 0:
                out[-1] = (out[-1][0], j + 1, 'c'); i = j + 1; incomment = None
            else:
                out[-1] = (out[-1][0], n, 'c'); i = n
        elif line.startswith('(*', i):
            j = line.find('*)', i + 2)
            if j >= 0:
                out.append((i, j + 2, 'c')); i = j + 2
            else:
                out.append((i, n, 'c')); incomment = '*)'; i = n
        elif ch == "'":
            j = i + 1
            while j < n:
                if line[j] == "'":
                    if j + 1 < n and line[j + 1] == "'": j += 2; continue
                    j += 1; break
                j += 1
            out.append((i, j, 's')); i = j
        elif ch.isalpha() or ch == '_':
            j = i
            while j < n and (line[j].isalnum() or line[j] == '_'): j += 1
            w = line[i:j].lower()
            if w in KEYWORDS: out.append((i, j, 'k'))
            elif w in BUILTIN: out.append((i, j, 'b'))
            i = j
        elif ch.isdigit():
            j = i
            while j < n and (line[j].isdigit() or line[j] == '.'): j += 1
            out.append((i, j, 'n')); i = j
        else:
            i += 1
    return out, incomment


class Editor:
    def __init__(self):
        self.lines = [""]
        self.cy = self.cx = 0
        self.top = self.left = 0
        self.name = None
        self.modified = False
        self.insert = True
        self.autoindent = True
        self.undo = []
        self.mark_b = self.mark_k = None   # (y, x)
        self.clip = []

    # ---- helpers
    def snapshot(self):
        self.undo.append((list(self.lines), self.cy, self.cx))
        if len(self.undo) > 300: self.undo.pop(0)

    def do_undo(self):
        if self.undo:
            self.lines, self.cy, self.cx = self.undo.pop()
            self.modified = True

    def text(self):
        return "\n".join(self.lines) + "\n"

    def load(self, path):
        with open(path, encoding='utf-8', errors='replace') as f:
            data = f.read()
        self.lines = data.replace('\r\n', '\n').split('\n')
        if len(self.lines) > 1 and self.lines[-1] == '': self.lines.pop()
        if not self.lines: self.lines = [""]
        self.name = path
        self.cy = self.cx = self.top = self.left = 0
        self.modified = False
        self.undo = []
        self.mark_b = self.mark_k = None

    def save(self, path=None):
        path = path or self.name
        with open(path, 'w', encoding='utf-8') as f:
            f.write(self.text())
        self.name = path
        self.modified = False

    # ---- editing
    def clampx(self):
        self.cx = max(0, min(self.cx, len(self.lines[self.cy])))

    def insert_char(self, ch):
        self.snapshot_if('ch')
        ln = self.lines[self.cy]
        if self.insert or self.cx >= len(ln):
            self.lines[self.cy] = ln[:self.cx] + ch + ln[self.cx:]
        else:
            self.lines[self.cy] = ln[:self.cx] + ch + ln[self.cx + 1:]
        self.cx += 1; self.modified = True

    last_op = None
    def snapshot_if(self, op):
        if self.last_op != op: self.snapshot()
        self.last_op = op

    def newline(self):
        self.snapshot(); self.last_op = None
        ln = self.lines[self.cy]
        indent = ''
        if self.autoindent:
            indent = re.match(r'\s*', ln).group(0)
            if self.cx < len(indent): indent = indent[:self.cx]
        self.lines[self.cy] = ln[:self.cx]
        self.lines.insert(self.cy + 1, indent + ln[self.cx:])
        self.cy += 1; self.cx = len(indent); self.modified = True

    def backspace(self):
        if self.cx > 0:
            self.snapshot_if('bs')
            ln = self.lines[self.cy]
            self.lines[self.cy] = ln[:self.cx - 1] + ln[self.cx:]
            self.cx -= 1; self.modified = True
        elif self.cy > 0:
            self.snapshot(); self.last_op = None
            prev = self.lines[self.cy - 1]
            self.cx = len(prev)
            self.lines[self.cy - 1] = prev + self.lines[self.cy]
            del self.lines[self.cy]; self.cy -= 1; self.modified = True

    def delete(self):
        ln = self.lines[self.cy]
        if self.cx < len(ln):
            self.snapshot_if('del')
            self.lines[self.cy] = ln[:self.cx] + ln[self.cx + 1:]; self.modified = True
        elif self.cy + 1 < len(self.lines):
            self.snapshot(); self.last_op = None
            self.lines[self.cy] = ln + self.lines[self.cy + 1]
            del self.lines[self.cy + 1]; self.modified = True

    def delete_line(self):
        self.snapshot(); self.last_op = None
        if len(self.lines) == 1: self.lines[0] = ""
        else:
            del self.lines[self.cy]
            if self.cy >= len(self.lines): self.cy = len(self.lines) - 1
        self.cx = 0; self.modified = True

    def delete_word(self):
        ln = self.lines[self.cy]
        m = re.compile(r'\w+\s*|\s+|.').match(ln, self.cx)
        if m:
            self.snapshot(); self.last_op = None
            self.lines[self.cy] = ln[:self.cx] + ln[m.end():]; self.modified = True

    def tab(self):
        n = 2 - self.cx % 2
        for _ in range(n): self.insert_char(' ')

    # ---- blocks
    def block(self):
        if self.mark_b is None or self.mark_k is None: return None
        a, b = self.mark_b, self.mark_k
        if b < a: a, b = b, a
        return a, b

    def block_text(self):
        bl = self.block()
        if not bl: return None
        (y1, x1), (y2, x2) = bl
        if y1 == y2: return [self.lines[y1][x1:x2]]
        out = [self.lines[y1][x1:]] + self.lines[y1 + 1:y2] + [self.lines[y2][:x2]]
        return out

    def delete_block(self):
        bl = self.block()
        if not bl: return
        self.snapshot(); self.last_op = None
        (y1, x1), (y2, x2) = bl
        self.lines[y1:y2 + 1] = [self.lines[y1][:x1] + self.lines[y2][x2:]]
        self.cy, self.cx = y1, x1
        self.mark_b = self.mark_k = None; self.modified = True

    def insert_text(self, parts):
        self.snapshot(); self.last_op = None
        ln = self.lines[self.cy]
        head, tail = ln[:self.cx], ln[self.cx:]
        if len(parts) == 1:
            self.lines[self.cy] = head + parts[0] + tail
            self.cx += len(parts[0])
        else:
            new = [head + parts[0]] + parts[1:-1] + [parts[-1] + tail]
            self.lines[self.cy:self.cy + 1] = new
            self.cy += len(parts) - 1; self.cx = len(parts[-1])
        self.modified = True

    # ---- search
    def find(self, pat, case=False, start=None):
        flags = 0 if case else re.I
        y, x = start if start else (self.cy, self.cx)
        rx = re.compile(re.escape(pat), flags)
        for yy in range(y, len(self.lines)):
            m = rx.search(self.lines[yy], x if yy == y else 0)
            if m: return yy, m.start(), m.end()
        for yy in range(0, y + 1):
            m = rx.search(self.lines[yy])
            if m: return yy, m.start(), m.end()
        return None


MENUS = [
    ("File", 'f', [("New", None, 'new'), ("Open...", "F3", 'open'), ("Save", "F2", 'save'),
                   ("Save as...", None, 'saveas'), ("Run DOS shell", None, 'shell'), ("Exit", "Alt-X", 'exit')]),
    ("Edit", 'e', [("Undo", "Ctrl-Z", 'undo'), ("Copy", "Ctrl-K C", 'copy'), ("Move", "Ctrl-K V", 'move'),
                   ("Delete block", "Ctrl-K Y", 'delblock'), ("Delete line", "Ctrl-Y", 'delline'),
                   ("Mark begin", "Ctrl-K B", 'markb'), ("Mark end", "Ctrl-K K", 'markk')]),
    ("Search", 's', [("Find...", "Ctrl-Q F", 'find'), ("Replace...", "Ctrl-Q A", 'replace'),
                     ("Search again", "Ctrl-L", 'again'), ("Go to line...", "Ctrl-Q G", 'goto')]),
    ("Run", 'r', [("Run", "Ctrl-R", 'run'), ("Program reset", None, 'reset'), ("Parameters...", None, 'params')]),
    ("Compile", 'c', [("Compile", "Alt-F9", 'make'), ("Make", "F9", 'make'), ("Show assembly", None, 'asm')]),
    ("Options", 'o', [("Auto indent", None, 'toggle_indent'), ("Syntax colours", None, 'toggle_colour')]),
    ("Help", 'h', [("Contents", "F1", 'help'), ("About...", None, 'about')]),
]


class IDE:
    def __init__(self, scr, path=None):
        self.scr = scr
        self.ed = Editor()
        self.msgs = []          # list of (line, text)
        self.msgsel = 0
        self.showmsgs = False
        self.params = ""
        self.colour = True
        self.status = ""
        self.lastfind = ""
        self.lastrepl = ""
        self.errline = None
        self.tmp = tempfile.mkdtemp(prefix="tpide.")
        self.bin = os.environ.get('CREXX_BIN') or os.path.dirname(shutil.which('rxvm') or '/usr/bin/rxvm')
        self.counter = 0
        curses.curs_set(1)
        self.init_colors()
        scr.keypad(True)
        try: curses.set_escdelay(40)
        except Exception: pass
        if path and os.path.exists(path):
            self.ed.load(path)
        elif path:
            self.ed.name = path
            self.ed.lines = SKELETON.rstrip('\n').split('\n')
        else:
            self.ed.lines = SKELETON.rstrip('\n').split('\n')
        self.ed.modified = False

    def init_colors(self):
        curses.start_color()
        try: curses.use_default_colors()
        except Exception: pass
        B, W, K, C, Y, R, G = (curses.COLOR_BLUE, curses.COLOR_WHITE, curses.COLOR_BLACK,
                               curses.COLOR_CYAN, curses.COLOR_YELLOW, curses.COLOR_RED, curses.COLOR_GREEN)
        pairs = {1: (Y, B), 2: (W, B), 3: (C, B), 4: (G, B), 5: (C, B), 6: (K, W), 7: (R, W),
                 8: (W, K), 9: (K, C), 10: (K, W), 11: (W, R), 12: (K, C), 13: (W, B), 14: (R, W), 15: (K, G)}
        for k, (f, b) in pairs.items(): curses.init_pair(k, f, b)
        self.A = {'text': curses.color_pair(1), 'k': curses.color_pair(2) | curses.A_BOLD,
                  'c': curses.color_pair(3), 's': curses.color_pair(4), 'n': curses.color_pair(5),
                  'b': curses.color_pair(1) | curses.A_BOLD,
                  'bar': curses.color_pair(6), 'hot': curses.color_pair(7) | curses.A_BOLD,
                  'sel': curses.color_pair(8), 'block': curses.color_pair(9),
                  'dlg': curses.color_pair(10), 'err': curses.color_pair(11),
                  'msg': curses.color_pair(12), 'frame': curses.color_pair(13) | curses.A_BOLD,
                  'dhot': curses.color_pair(14) | curses.A_BOLD, 'ok': curses.color_pair(15)}

    # ---------------------------------------------------------------- drawing
    def size(self):
        h, w = self.scr.getmaxyx()
        return h, w

    def put(self, y, x, s, attr):
        h, w = self.size()
        if y < 0 or y >= h or x >= w: return
        s = s[:max(0, w - x)]
        try: self.scr.addstr(y, x, s, attr)
        except curses.error: pass

    def draw_menubar(self, active=-1):
        h, w = self.size()
        self.put(0, 0, " " * w, self.A['bar'])
        x = 2
        for i, (name, key, _) in enumerate(MENUS):
            attr = self.A['sel'] if i == active else self.A['bar']
            self.put(0, x - 1, " ", attr)
            self.put(0, x, name[0], self.A['sel'] if i == active else self.A['hot'])
            self.put(0, x + 1, name[1:], attr)
            self.put(0, x + len(name), " ", attr)
            x += len(name) + 3

    def draw_status(self):
        h, w = self.size()
        s = " F1 Help  F2 Save  F3 Open  F9 Make  ^R Run  F10 Menu  Alt-X Exit"
        self.put(h - 1, 0, (s + " " * w)[:w], self.A['bar'])
        if self.status:
            m = " " + self.status + " "
            self.put(h - 1, max(0, w - len(m) - 1), m, self.A['hot'] | curses.A_REVERSE if False else self.A['err'])

    def edit_rows(self):
        h, w = self.size()
        mh = 0
        if self.showmsgs:
            mh = min(8, max(4, len(self.msgs) + 2))
        return 1, h - 2 - mh   # first row, last row (frame included)

    def draw_editor(self):
        ed = self.ed
        h, w = self.size()
        r0, r1 = self.edit_rows()
        rows = r1 - r0 - 1
        cols = w - 2
        # keep cursor visible
        if ed.cy < ed.top: ed.top = ed.cy
        if ed.cy >= ed.top + rows: ed.top = ed.cy - rows + 1
        if ed.cx < ed.left: ed.left = ed.cx
        if ed.cx >= ed.left + cols - 1: ed.left = ed.cx - cols + 2
        fr = self.A['frame']
        title = ed.name and os.path.basename(ed.name) or "NONAME.PAS"
        if ed.modified: title += " *"
        top = "╔" + "═" * (w - 2) + "╗"
        self.put(r0, 0, top, fr)
        t = " " + title + " "
        self.put(r0, (w - len(t)) // 2, t, fr)
        self.put(r0, 2, "[■]", fr)
        for i in range(rows):
            self.put(r0 + 1 + i, 0, "║", fr)
            self.put(r0 + 1 + i, w - 1, "║", fr)
        self.put(r1, 0, "╚" + "═" * (w - 2) + "╝", fr)
        pos = " %d:%d " % (ed.cy + 1, ed.cx + 1)
        self.put(r1, 2, pos, fr)
        self.put(r1, 14, " Insert " if ed.insert else " Overwrite ", fr)
        # text
        comment = None
        states = []
        for y in range(0, min(len(ed.lines), ed.top + rows)):
            spans, comment = classify_line(ed.lines[y], comment) if self.colour else ([], None)
            states.append(spans)
        bl = ed.block()
        for i in range(rows):
            y = ed.top + i
            row = r0 + 1 + i
            self.put(row, 1, " " * cols, self.A['text'])
            if y >= len(ed.lines): continue
            line = ed.lines[y]
            vis = line[ed.left:ed.left + cols]
            self.put(row, 1, vis, self.A['text'])
            if self.colour:
                for (a, b, kind) in states[y]:
                    a2, b2 = max(a, ed.left), min(b, ed.left + cols)
                    if a2 < b2: self.put(row, 1 + a2 - ed.left, line[a2:b2], self.A[kind])
            if bl:
                (y1, x1), (y2, x2) = bl
                if y1 <= y <= y2:
                    a = x1 if y == y1 else 0
                    b = x2 if y == y2 else len(line) + 1
                    a2, b2 = max(a, ed.left), min(b, ed.left + cols)
                    if a2 < b2:
                        seg = (line + " ")[a2:b2]
                        self.put(row, 1 + a2 - ed.left, seg, self.A['block'])
            if self.errline == y:
                self.put(row, 1, (line + " " * cols)[ed.left:ed.left + cols], self.A['err'])
        # messages window
        if self.showmsgs:
            mh = h - 2 - r1
            self.put(r1 + 1, 0, "╔" + "═" * (w - 2) + "╗", fr)
            self.put(r1 + 1, 2, " Messages ", fr)
            for i in range(mh - 2):
                self.put(r1 + 2 + i, 0, "║" + " " * (w - 2) + "║", fr)
                if i < len(self.msgs):
                    ln, txt = self.msgs[i]
                    attr = self.A['sel'] if i == self.msgsel else self.A['msg']
                    self.put(r1 + 2 + i, 1, (txt + " " * w)[:w - 2], attr)
        self.draw_status()
        self.scr.move(r0 + 1 + (ed.cy - ed.top), 1 + ed.cx - ed.left)

    def redraw(self, menu=-1):
        self.scr.erase()
        self.draw_menubar(menu)
        self.draw_editor()
        self.scr.refresh()

    # ---------------------------------------------------------------- input
    def getkey(self):
        k = self.scr.get_wch() if hasattr(self.scr, 'get_wch') else self.scr.getch()
        if k == '\x1b':
            self.scr.nodelay(True)
            try: k2 = self.scr.get_wch()
            except curses.error: k2 = None
            self.scr.nodelay(False)
            if k2 is None: return 'ESC'
            if isinstance(k2, str) and len(k2) == 1: return 'ALT-' + k2.lower()
            return k2
        return k

    def box(self, title, lines, w=None, h=None, attr=None, wait=True):
        sh, sw = self.size()
        w = w or min(sw - 4, max(len(title) + 6, max((len(l) for l in lines), default=0) + 4))
        h = h or len(lines) + 4
        y0, x0 = max(0, (sh - h) // 2), max(0, (sw - w) // 2)
        a = attr or self.A['dlg']
        self.put(y0, x0, "┌" + "─" * (w - 2) + "┐", a)
        t = " " + title + " "
        self.put(y0, x0 + (w - len(t)) // 2, t, a)
        for i in range(1, h - 1):
            self.put(y0 + i, x0, "│" + " " * (w - 2) + "│", a)
        self.put(y0 + h - 1, x0, "└" + "─" * (w - 2) + "┘", a)
        for i, l in enumerate(lines):
            self.put(y0 + 2 + i, x0 + 2, l[:w - 4], a)
        return y0, x0, w, h

    def message(self, title, lines):
        self.redraw()
        y0, x0, w, h = self.box(title, lines + ["", "     [ Press any key ]"])
        self.scr.refresh()
        self.getkey()

    def prompt(self, title, default=""):
        buf = default
        sh, sw = self.size()
        while True:
            self.redraw()
            w = min(sw - 4, 60)
            y0, x0, w, h = self.box(title, ["", "", ""], w=w, h=6)
            self.put(y0 + 2, x0 + 2, (buf + "_" + " " * w)[:w - 4], self.A['sel'])
            self.scr.refresh()
            k = self.getkey()
            if k in ('\n', '\r', curses.KEY_ENTER): return buf
            if k in ('ESC', '\x03'): return None
            if k in (curses.KEY_BACKSPACE, '\x7f', '\b'): buf = buf[:-1]
            elif isinstance(k, str) and len(k) == 1 and k.isprintable(): buf += k

    def confirm(self, text):
        while True:
            self.redraw()
            self.box("Confirm", ["", text, "", "   [Y]es   [N]o   Esc=cancel"])
            self.scr.refresh()
            k = self.getkey()
            if isinstance(k, str) and k.lower() == 'y': return True
            if isinstance(k, str) and k.lower() == 'n': return False
            if k == 'ESC': return None

    def choose_file(self):
        files = sorted(f for f in os.listdir('.') if f.lower().endswith(('.pas', '.pp', '.inc')))
        sel, top = 0, 0
        while True:
            self.redraw()
            vis = 10
            lines = ["Name:" + " " * 30] + [("> " if i == sel else "  ") + f for i, f in enumerate(files[top:top + vis], top)]
            if not files: lines.append("  (no .pas files here; press N to type a name)")
            y0, x0, w, h = self.box("Open a File", lines + ["", "Enter=open  N=type name  Esc=cancel"], w=50)
            self.scr.refresh()
            k = self.getkey()
            if k == 'ESC': return None
            if k in (curses.KEY_DOWN,) and sel + 1 < len(files): sel += 1
            elif k == curses.KEY_UP and sel > 0: sel -= 1
            if sel < top: top = sel
            if sel >= top + vis: top = sel - vis + 1
            if k in ('\n', '\r') and files: return files[sel]
            if isinstance(k, str) and k.lower() == 'n':
                return self.prompt("Open file name", "")

    # ---------------------------------------------------------------- actions
    def check_save(self):
        if not self.ed.modified: return True
        r = self.confirm("Save changes to %s?" % (self.ed.name or "NONAME.PAS"))
        if r is None: return False
        if r: return self.do('save')
        return True

    def do(self, act):
        ed = self.ed
        self.status = ""
        if act == 'new':
            if not self.check_save(): return True
            ed.__init__(); ed.lines = SKELETON.rstrip('\n').split('\n'); self.msgs = []; self.showmsgs = False
        elif act == 'open':
            if not self.check_save(): return True
            f = self.choose_file()
            if f:
                try: ed.load(f); self.showmsgs = False; self.errline = None
                except Exception as e: self.message("Error", [str(e)])
        elif act == 'save':
            if not ed.name: return self.do('saveas')
            try: ed.save(); self.status = "Saved"
            except Exception as e: self.message("Error", [str(e)]); return False
        elif act == 'saveas':
            f = self.prompt("Save file as", ed.name or "noname.pas")
            if not f: return False
            if '.' not in os.path.basename(f): f += '.pas'
            try: ed.save(f)
            except Exception as e: self.message("Error", [str(e)]); return False
        elif act == 'exit':
            if self.check_save(): return 'quit'
        elif act == 'undo': ed.do_undo()
        elif act == 'markb': ed.mark_b = (ed.cy, ed.cx)
        elif act == 'markk': ed.mark_k = (ed.cy, ed.cx)
        elif act == 'copy':
            t = ed.block_text()
            if t: ed.insert_text(t)
            else: self.status = "No block marked"
        elif act == 'move':
            t = ed.block_text()
            if t:
                bl = ed.block(); y, x = ed.cy, ed.cx
                ed.insert_text(t)
                # delete the original (positions may have shifted when inserting before it)
                nl = len(t) - 1
                (y1, x1), (y2, x2) = bl
                if (y, x) <= (y1, x1):
                    ed.mark_b = (y1 + nl, x1 if y1 > y else x1 + len(t[-1]) if nl == 0 and y1 == y else x1)
                    ed.mark_k = (y2 + nl, x2)
                ed.delete_block()
        elif act == 'delblock': ed.delete_block()
        elif act == 'delline': ed.delete_line()
        elif act == 'find':
            s = self.prompt("Find text", self.lastfind)
            if s:
                self.lastfind = s; self.do('again')
        elif act == 'again':
            if not self.lastfind: return self.do('find')
            r = ed.find(self.lastfind, start=(ed.cy, ed.cx + (1 if True else 0)))
            if r: ed.cy, ed.cx = r[0], r[1]; ed.mark_b = (r[0], r[1]); ed.mark_k = (r[0], r[2])
            else: self.status = "Search string not found"
        elif act == 'replace':
            s = self.prompt("Text to find", self.lastfind)
            if not s: return True
            t = self.prompt("New text", self.lastrepl)
            if t is None: return True
            self.lastfind, self.lastrepl = s, t
            n = 0
            ed.snapshot()
            for i, ln in enumerate(ed.lines):
                new, c = re.subn(re.escape(s), t.replace('\\', '\\\\'), ln, flags=re.I)
                if c: ed.lines[i] = new; n += c
            if n: ed.modified = True
            self.status = "%d replaced" % n
        elif act == 'goto':
            s = self.prompt("Line number", "")
            if s and s.strip().isdigit():
                ed.cy = max(0, min(len(ed.lines) - 1, int(s) - 1)); ed.clampx()
        elif act == 'make': self.compile()
        elif act == 'run': self.run()
        elif act == 'reset': self.status = "Program reset"
        elif act == 'params':
            s = self.prompt("Program parameters", self.params)
            if s is not None: self.params = s
        elif act == 'asm': self.show_asm()
        elif act == 'toggle_indent':
            ed.autoindent = not ed.autoindent; self.status = "Auto indent " + ("on" if ed.autoindent else "off")
        elif act == 'toggle_colour':
            self.colour = not self.colour
        elif act == 'help': self.help()
        elif act == 'about':
            self.message("About", ["Turbo Pascal for cREXX", "", "Editor and environment written in Python,",
                                   "compiler written in cREXX Level B.", "", "Pascal -> cREXX assembly -> rxas -> rxvm"])
        elif act == 'shell':
            self.suspend(lambda: subprocess.call(os.environ.get('SHELL', '/bin/sh')))
        return True

    def help(self):
        lines = HELP.split('\n'); top = 0
        while True:
            self.scr.erase()
            h, w = self.size()
            self.put(0, 0, " Help ".center(w), self.A['bar'])
            for i in range(h - 2):
                if top + i < len(lines): self.put(1 + i, 0, lines[top + i][:w], self.A['text'])
            self.put(h - 1, 0, " Up/Down PgUp/PgDn scroll   Esc close".ljust(w), self.A['bar'])
            self.scr.refresh()
            k = self.getkey()
            if k in ('ESC', 'q'): return
            if k == curses.KEY_DOWN: top = min(max(0, len(lines) - 5), top + 1)
            elif k == curses.KEY_UP: top = max(0, top - 1)
            elif k == curses.KEY_NPAGE: top = min(max(0, len(lines) - 5), top + h - 3)
            elif k == curses.KEY_PPAGE: top = max(0, top - h + 3)

    # ---------------------------------------------------------------- build
    def stem(self):
        return os.path.join(self.tmp, "prog")

    def compile(self):
        ed = self.ed
        src = self.stem() + ".pas"
        with open(src, 'w', encoding='utf-8') as f: f.write(ed.text())
        self.redraw()
        self.box("Compiling", ["", "Compiling " + os.path.basename(ed.name or "noname.pas") + " ...", ""], w=44)
        self.scr.refresh()
        env = dict(os.environ)
        if self.bin: env['PATH'] = self.bin + os.pathsep + env.get('PATH', '')
        r = subprocess.run(["rxvm", os.path.join(ROOT, "build", "pascal.rxbin"), "-a", src, self.stem() + ".rxas"],
                           capture_output=True, text=True, env=env, cwd=self.tmp)
        out = (r.stdout + r.stderr).strip()
        self.msgs = []; self.errline = None
        if r.returncode != 0:
            for l in out.split('\n'):
                m = re.search(r'\((\d+)\): (error|warning): (.*)', l)
                if m: self.msgs.append((int(m.group(1)) - 1, "%s %s: %s" % (
                    "Error" if m.group(2) == 'error' else "Warning", m.group(1), m.group(3))))
                elif l.strip(): self.msgs.append((None, l.strip()))
            self.showmsgs = True; self.msgsel = 0
            for ln, _ in self.msgs:
                if ln is not None:
                    ed.cy = max(0, min(len(ed.lines) - 1, ln)); ed.clampx(); self.errline = ln
                    break
            self.status = "Compile failed"
            return False
        r = subprocess.run(["rxas", "prog"], capture_output=True, text=True, env=env, cwd=self.tmp)
        if r.returncode != 0:
            self.msgs = [(None, l.strip()) for l in (r.stdout + r.stderr).split('\n') if l.strip()]
            self.showmsgs = True; self.status = "Assembly failed"
            return False
        self.msgs = [(None, "Compile successful: %d lines." % len(ed.lines))]
        self.showmsgs = True; self.msgsel = 0
        self.status = "Compile successful"
        return True

    def suspend(self, fn):
        curses.def_prog_mode(); curses.endwin()
        try: fn()
        finally:
            curses.reset_prog_mode(); self.scr.refresh()

    def run(self):
        if not self.compile(): return
        env = dict(os.environ)
        if self.bin: env['PATH'] = self.bin + os.pathsep + env.get('PATH', '')
        args = self.params.split()
        def go():
            os.system('clear')
            rc = subprocess.call(["rxvm", "prog.rxbin", os.path.join(ROOT, "build", "pasrt.rxbin"), "-a"] + args,
                                 env=env, cwd=self.tmp)
            print("\n[Program finished, exit code %d. Press Enter to return to the IDE]" % rc, end='', flush=True)
            try: input()
            except EOFError: pass
        self.suspend(go)
        self.showmsgs = False

    def show_asm(self):
        if not self.compile(): return
        try: lines = open(self.stem() + ".rxas").read().split('\n')
        except Exception as e: self.message("Error", [str(e)]); return
        top = 0
        while True:
            self.scr.erase(); h, w = self.size()
            self.put(0, 0, " Generated cREXX assembly ".center(w), self.A['bar'])
            for i in range(h - 2):
                if top + i < len(lines): self.put(1 + i, 0, lines[top + i][:w], self.A['text'])
            self.put(h - 1, 0, " Up/Down PgUp/PgDn scroll   Esc close".ljust(w), self.A['bar'])
            self.scr.refresh(); k = self.getkey()
            if k == 'ESC': return
            if k == curses.KEY_DOWN: top = min(len(lines) - 1, top + 1)
            elif k == curses.KEY_UP: top = max(0, top - 1)
            elif k == curses.KEY_NPAGE: top = min(len(lines) - 1, top + h - 3)
            elif k == curses.KEY_PPAGE: top = max(0, top - h + 3)

    # ---------------------------------------------------------------- menus
    def menu(self, start=0):
        i = start
        j = 0
        while True:
            name, key, items = MENUS[i]
            self.redraw(i)
            h, w = self.size()
            x = 1
            for n in range(i): x += len(MENUS[n][0]) + 3
            width = max(len(a) + len(b or '') for a, b, _ in items) + 8
            self.put(1, x, "┌" + "─" * (width - 2) + "┐", self.A['bar'])
            for n, (label, k2, act) in enumerate(items):
                attr = self.A['sel'] if n == j else self.A['bar']
                line = " " + label + " " * (width - 3 - len(label) - len(k2 or '')) + (k2 or '') + " "
                self.put(2 + n, x, "│", self.A['bar']); self.put(2 + n, x + 1, line[:width - 2], attr)
                self.put(2 + n, x + width - 1, "│", self.A['bar'])
            self.put(2 + len(items), x, "└" + "─" * (width - 2) + "┘", self.A['bar'])
            self.scr.refresh()
            k = self.getkey()
            if k == 'ESC' or k == curses.KEY_F10: return None
            if k == curses.KEY_DOWN: j = (j + 1) % len(items)
            elif k == curses.KEY_UP: j = (j - 1) % len(items)
            elif k == curses.KEY_RIGHT: i = (i + 1) % len(MENUS); j = 0
            elif k == curses.KEY_LEFT: i = (i - 1) % len(MENUS); j = 0
            elif k in ('\n', '\r'): return items[j][2]
            elif isinstance(k, str) and k.startswith('ALT-'):
                for n, m in enumerate(MENUS):
                    if m[1] == k[4]: i = n; j = 0

    # ---------------------------------------------------------------- main loop
    def loop(self):
        ed = self.ed
        prefix = None
        while True:
            self.redraw()
            k = self.getkey()
            ed_status_keep = self.status
            self.status = ""
            act = None
            # two-key WordStar commands
            if prefix:
                p, prefix = prefix, None
                c = k.lower() if isinstance(k, str) else k
                if isinstance(c, str) and len(c) == 1 and ord(c) < 32: c = chr(ord(c) + 96)
                if p == 'k':
                    act = {'b': 'markb', 'k': 'markk', 'c': 'copy', 'v': 'move', 'y': 'delblock',
                           's': 'save', 'x': 'exit', 'd': 'save'}.get(c)
                    if c == 'r':
                        f = self.prompt("Read block from file", "")
                        if f and os.path.exists(f): ed.insert_text(open(f).read().rstrip('\n').split('\n'))
                    if c == 'w':
                        t = ed.block_text()
                        f = self.prompt("Write block to file", "")
                        if f and t: open(f, 'w').write("\n".join(t) + "\n")
                elif p == 'q':
                    act = {'f': 'find', 'a': 'replace', 'g': 'goto'}.get(c)
                if act and self.do(act) == 'quit': return
                continue
            if k == curses.KEY_RESIZE: continue
            if k == 'ALT-x': 
                if self.do('exit') == 'quit': return
                continue
            if isinstance(k, str) and k.startswith('ALT-'):
                for n, m in enumerate(MENUS):
                    if m[1] == k[4]:
                        a = self.menu(n)
                        if a and self.do(a) == 'quit': return
                continue
            if k == curses.KEY_F10:
                a = self.menu(0)
                if a and self.do(a) == 'quit': return
                continue
            fmap = {curses.KEY_F1: 'help', curses.KEY_F2: 'save', curses.KEY_F3: 'open',
                    curses.KEY_F9: 'make', curses.KEY_F5: 'run'}
            if k in fmap: self.do(fmap[k]); continue
            if k == curses.KEY_F0 + 33: self.do('run'); continue
            if isinstance(k, str) and len(k) == 1:
                o = ord(k)
                if o == 11: prefix = 'k'; self.status = "^K"; continue
                if o == 17: prefix = 'q'; self.status = "^Q"; continue
                if o == 18: self.do('run'); continue
                if o == 26: self.do('undo'); continue
                if o == 25: self.do('delline'); continue
                if o == 12: self.do('again'); continue
                if o == 20: ed.delete_word(); continue
                if o == 19: ed.cx = max(0, ed.cx - 1); continue
                if o in (10, 13): self.show_msg_jump() or ed.newline(); continue
                if o == 9: ed.tab(); continue
                if o in (127, 8): ed.backspace(); continue
                if k.isprintable(): ed.insert_char(k); continue
                continue
            # cursor keys
            if k == curses.KEY_UP: ed.cy = max(0, ed.cy - 1); ed.clampx()
            elif k == curses.KEY_DOWN: ed.cy = min(len(ed.lines) - 1, ed.cy + 1); ed.clampx()
            elif k == curses.KEY_LEFT:
                if ed.cx > 0: ed.cx -= 1
                elif ed.cy > 0: ed.cy -= 1; ed.cx = len(ed.lines[ed.cy])
            elif k == curses.KEY_RIGHT:
                if ed.cx < len(ed.lines[ed.cy]): ed.cx += 1
                elif ed.cy + 1 < len(ed.lines): ed.cy += 1; ed.cx = 0
            elif k == curses.KEY_HOME: ed.cx = 0
            elif k == curses.KEY_END: ed.cx = len(ed.lines[ed.cy])
            elif k == curses.KEY_PPAGE: ed.cy = max(0, ed.cy - 15); ed.clampx()
            elif k == curses.KEY_NPAGE: ed.cy = min(len(ed.lines) - 1, ed.cy + 15); ed.clampx()
            elif k == curses.KEY_BACKSPACE: ed.backspace()
            elif k == curses.KEY_DC: ed.delete()
            elif k == curses.KEY_IC: ed.insert = not ed.insert
            elif k == curses.KEY_ENTER: ed.newline()
            elif k == 'ESC' and self.showmsgs: self.showmsgs = False; self.errline = None

    def show_msg_jump(self):
        return False


def main(stdscr, path):
    ide = IDE(stdscr, path)
    try:
        ide.loop()
    finally:
        shutil.rmtree(ide.tmp, ignore_errors=True)


if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else None
    if path in ('-h', '--help'):
        print("usage: tp [file.pas]"); sys.exit(0)
    os.environ.setdefault('ESCDELAY', '40')
    curses.wrapper(main, path)
