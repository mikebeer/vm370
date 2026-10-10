#!/usr/bin/env python3
"""cmdtables.py -- write docs/50-COMMANDS.md, the CP and CMS command tables.

CP:  read off DMKCFC as it is built -- the CE source with this module's update
     decks applied in AUXLCL order -- so the table is the dispatcher's own:
     the COMND table (name, minimum abbreviation, classes, routine) and the
     QUERY / SET operand lists (QRYLIST / SETLIST: name, minimum length,
     classes, module).
CMS: the nucleus functions from DMSFNC's JFUN table, and the MODULE and EXEC
     files on the system disks from a LISTFILE of a running system
     (docs/data/cms-disks-b6.txt: MAINT under IPL 190; S = 190, U = 19D,
     Y = 19E).
The one-line descriptions and the VM/370plus marks are below; a command
without a description is listed all the same.

    python3 arch/31bit/tools/cmdtables.py            (writes the file)
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
CPSRC = '/home/claude/vmce/source/cp/DMKCFC.ASSEMBLE'
CMSSRC = '/home/claude/vmce/source/cms/DMSFNC.ASSEMBLE'
UPD = os.path.join(REPO, 'arch', '31bit', 'updates')
DISKS = os.path.join(REPO, 'docs', 'data', 'cms-disks-b6.txt')
OUT = os.path.join(REPO, 'docs', '50-COMMANDS.md')


def apply_updates(src, module):
    """CE source plus the module's decks (AUXLCL order, oldest first)."""
    recs = [(l[72:80], l[:72]) for l in
            open(src, encoding='latin-1').read().split('\n') if l.strip()]
    auxf = os.path.join(UPD, module + '.AUXLCL')
    decks = []
    if os.path.exists(auxf):
        decks = [l.split()[0] for l in open(auxf) if l.strip()][::-1]
    for d in decks:
        p = os.path.join(UPD, '%s.%s' % (module, d))
        lines = open(p, encoding='latin-1').read().split('\n')
        i = 0
        while i < len(lines):
            l = lines[i]
            m = re.match(r'\./ ([IRD]) (\d{8})(?: (\d{8}))?', l)
            if not m:
                i += 1
                continue
            op, a, b = m.group(1), m.group(2), m.group(3)
            i += 1
            body = []
            while i < len(lines) and not lines[i].startswith('./') and \
                    lines[i].strip():
                body.append((lines[i][72:80], lines[i][:72]))
                i += 1
            ix = [k for k, r in enumerate(recs) if r[0] == a][0]
            if op == 'I':
                recs[ix + 1:ix + 1] = body
            else:
                jx = ix if not b else [k for k, r in enumerate(recs)
                                       if r[0] == b][0]
                recs[ix:jx + 1] = body if op == 'R' else []
    return [r[1] for r in recs], decks


def classes(expr):
    e = expr.strip('()')
    if e in ('0', ''):
        return 'any'
    return ''.join(sorted(x for x in e.split('+') if x))


CPDESC = {
    'LOGON': 'log on to a virtual machine', 'LOGIN': 'synonym of LOGON',
    'DIAL': 'connect a terminal to a multi-access virtual machine',
    'ATTACH': 'attach a real device to a virtual machine',
    'ATTN': 'enter CP (attention) from a virtual console',
    'ADSTOP': 'set an address stop', 'ACNT': 'create accounting records now',
    'AUTOLOG': 'log on a virtual machine disconnected',
    'BEGIN': 'resume the virtual machine', 'BACKSPAC': 'backspace a spooled printer or punch',
    'CHANGE': 'change attributes of spool files', 'CLOSE': 'close a virtual spool device',
    'COUPLE': 'connect two virtual channel-to-channel adapters',
    'DISPLAY': 'display storage, registers, PSW, keys',
    'DCP': 'display real (CP) storage', 'DEFINE': 'define virtual storage or devices',
    'DETACH': 'detach a real or virtual device', 'DISCONN': 'disconnect the terminal, keep the machine running',
    'DISABLE': 'disable lines for logon', 'DMCP': 'dump real (CP) storage to the reader',
    'DRAIN': 'drain a spooling device', 'DUMP': 'dump virtual storage to the reader',
    'ECHO': 'terminal echo test', 'EXTERNAL': 'present an external interrupt',
    'ENABLE': 'enable lines for logon', 'FLUSH': 'cancel the current spool output',
    'FORCE': 'log off another user', 'HALT': 'halt a real device',
    'HCP': 'CE: run a Hercules command', 'HOLD': 'hold spool files',
    'IPL': 'IPL a device or a saved system',
    'LINK': 'link to another user\'s minidisk',
    'LOADBUF': 'load a printer UCS/FCB buffer', 'LOADVFCB': 'load a virtual printer FCB',
    'LOCATE': 'locate CP control blocks', 'LOCK': 'lock pages in real storage',
    'LOGOFF': 'end the session', 'LOGOUT': 'synonym of LOGOFF',
    'MONITOR': 'start/stop the system monitor', 'MSG': 'send a message',
    'MSGNOH': 'send a message without header', 'MESSAGE': 'synonym of MSG',
    'NETWORK': 'control 3270 and RSCS lines', 'NOTREADY': 'make a virtual device not ready',
    'ORDER': 'reorder spool files', 'PURGE': 'purge spool files',
    'QUERY': 'query status (operands below)', 'READY': 'present device end on a virtual device',
    'FREE': 'release held spool files', 'REPEAT': 'repeat a printer file',
    'REQUEST': 'present an attention to the virtual console',
    'RESET': 'reset a virtual device', 'REWIND': 'rewind a tape',
    'SYSTEM': 'reset/clear/restart the virtual machine',
    'SAVESYS': 'save a named system', 'INDICATE': 'system load and user resource use',
    'TRANSFER': 'transfer spool files to another user',
    'SET': 'set options (operands below)', 'SHUTDOWN': 'shut the system down',
    'SLEEP': 'put the virtual machine to sleep', 'SPACE': 'single-space a printer file',
    'SPOOL': 'set spooling options', 'STORE': 'store into storage, registers, PSW',
    'START': 'start a spooling device', 'STCP': 'store into real (CP) storage',
    'TAG': 'set spool file tags', 'TERMINAL': 'set terminal characteristics',
    'TRACE': 'trace virtual machine events', 'PER': 'PER tracing (CE)',
    'UNLOCK': 'unlock pages', 'VARY': 'vary devices online/offline',
    'VMDUMP': 'dump virtual storage in VMDUMP format',
    'WNG': 'send a warning', 'WARNING': 'synonym of WNG',
    'SMSG': 'send a special message (VMCF)',
    '*': 'comment', 'CP': 'pass a command to CP',
}
CPPLUS = {
    'IPL': '**+** `IPL LINUX`: SET MACHINE ESA and IPL 250 (M7.10)',
    'DEFINE': '**+** `DEFINE STORAGE` above 16 MB (to 256M)',
    'DISPLAY': '**+** addresses above 16 MB',
    'STORE': '**+** addresses above 16 MB',
}
QPLUS = {'MACHINE': '**+** MACHINE 370 / ESA / 370, ESA PENDING (z/VM name)',
         'SET': '**+** line 5: ESA ON / PENDING / OFF'}
SPLUS = {'ESA': '**+** ON / OFF: ESA/390 architecture at the next IPL (M7)',
         'MACHINE': '**+** 370 / XA / ESA (z/VM name; SET ESA is the synonym)'}
QMOD = {0: 'DMKCQG', 4: 'DMKCQP', 8: 'DMKCQR', 12: 'DMKCQY', 20: 'DMKJRL',
        24: 'DMKCQH', 28: 'HDKCQU', 32: 'HDKCQA'}
SMOD = {0: 'DMKCFS', 4: 'DMKCFO', 12: 'DMKJRL'}

CMSDESC = {
    'ACCESS': 'access a minidisk', 'AMSERV': 'VSAM access method services',
    'ASSEMBLE': 'assembler (IFOX00)', 'ASMAHL': 'High Level Assembler-compatible assembler',
    'ASSGN': 'assign DOS logical units', 'CMSBATCH': 'CMS batch facility',
    'COMPARE': 'compare files', 'COPYFILE': 'copy files', 'DDR': 'DASD dump/restore',
    'DIRECT': 'CP directory program', 'DISK': 'DISK DUMP / LOAD via the punch/reader',
    'DLBL': 'define a DOS/VSAM label', 'EDIT': 'the CMS editor', 'EXECIO': 'EXEC I/O (disk, reader, CP)',
    'EXECUTIL': 'EXEC utilities', 'FILEDEF': 'define an OS file', 'FORMAT': 'format a minidisk',
    'GENMOD': 'generate a MODULE', 'GLOBAL': 'set MACLIB/TXTLIB/LOADLIB search', 'HNDINT': 'handle interrupts',
    'LISTFILE': 'list files', 'LISTIO': 'list DOS assignments', 'LKED': 'linkage editor',
    'MACLIB': 'maintain macro libraries', 'MOVEFILE': 'move data between devices',
    'PRINT': 'print a file', 'PUNCH': 'punch a file', 'QUERY': 'query CMS settings',
    'READCARD': 'read a reader file to disk', 'RELEASE': 'release a minidisk',
    'RENAME': 'rename files', 'SET': 'set CMS options', 'SORT': 'sort a file',
    'SYNONYM': 'set command synonyms', 'TAPE': 'tape utilities', 'TXTLIB': 'maintain text libraries',
    'TYPE': 'type a file', 'UPDATE': 'apply update decks', 'VMFPLC2': 'tape load/dump',
    'ZAP': 'patch modules', 'ERASE': 'erase files', 'STATE': 'is a file there?',
    'EXEC': 'run an EXEC', 'LOAD': 'load TEXT files', 'INCLUDE': 'load more TEXT files',
    'START': 'start a loaded program', 'LOADMOD': 'load a MODULE', 'FINIS': 'close files',
    'MAKEBUF': 'new console stack buffer', 'DROPBUF': 'drop stack buffers',
    'SENTRIES': 'number of stacked lines', 'DESBUF': 'clear the console stack',
    'IDENTIFY': 'user, node and time', 'NUCEXT': 'nucleus extensions',
    'SUBCOM': 'subcommand environments', 'CP': 'pass a command to CP', 'DEBUG': 'CMS debug environment',
    'FETCH': 'fetch a DOS phase',
    'ATTN': 'stack a line (program call)', 'CARDPH': 'punch a card (program call)',
    'CARDRD': 'read a card (program call)', 'CMSTIME': 'time of day (program call)',
    'CONREAD': 'console read (program call)', 'CONWAIT': 'wait for console I/O (program call)',
    'POINT': 'position in a file (program call)', 'PRINTIO': 'print I/O (program call)',
    'PRINTR': 'print a line (program call)', 'RDBUF': 'read a record (program call)',
    'WRBUF': 'write a record (program call)', 'RETURN': 'return to CMS (program call)',
    'STATEW': 'STATE, writable disks only', 'SUBSET': 'CMS subset (CMS-only commands)',
    'SVCFREE': 'get storage (program call)', 'SVCFRET': 'free storage (program call)',
    'TAPEIO': 'tape I/O (program call)', 'TRAP': 'trap I/O (program call)',
    'TYPLIN': 'type a line (program call)', 'VMNET': 'VNET/RSCS interface',
    'WAIT': 'wait for devices (program call)', 'WAITRD': 'read with wait (program call)', 'EDMAIN': 'EDIT main module',
    # 19E (Y): CE and community tools
    'EE$D': 'MECAFF EE editor (full screen)', 'EE$S': 'MECAFF FSLIST / FSVIEW',
    'BREXX': 'BREXX', 'GCC': 'GCC for CMS (C)', 'GCCE': 'GCC compile and run',
    'FLIST': 'CE full-screen file list (FLISTREP/REV)', 'XLIST': 'MECAFF file list',
    'XXLIST': 'MECAFF file list (extended)', 'MAIL': 'send mail (spool)',
    'SENDFILE': 'send a file (spool)', 'RECEIVE': 'receive a reader file',
    'PASCAL': 'Pascal/VS-style compiler', 'FORTRAN': 'FORTRAN G', 'FORTRANH': 'FORTRAN H',
    'COBOL': 'COBOL (IKFCBL00)', 'PLI': 'PL/I', 'WATFIV': 'WATFIV', 'SNOBOL4': 'SNOBOL4',
    'FORTH': 'Forth', 'BASIC': 'BASIC', 'BWBASIC': 'Bywater BASIC', 'PL360': 'PL360',
    'SCRIPT': 'SCRIPT text formatter', 'VMARC': 'VMARC archives', 'MINIZIP': 'zip', 'MINIUNZ': 'unzip',
    'DIFF': 'diff', 'SED': 'sed', 'M4': 'm4', 'FLEX': 'flex', 'BISON': 'bison', 'HEXDUMP': 'hex dump',
    'REXXTRY': 'try REXX statements',
    # 19D (U): VM/370plus
    'WAKEUP': '**+** wait for a reader file or a time (rc 2 time, 3 reader)',
    'CHAT': '**+** ask the CHATBOT service machine',
    'LINUX': '**+** IPL the Debian disk (`LINUX`, `LINUX READER`)',
    'FULIST': '**+** full-screen file list in the manner of FILELIST',
    'FL': '**+** synonym of FULIST', 'RXBVM8': '**+** cREXX VM (native CMS)',
    'UNHEX': '**+** hex text to binary', 'HELP': 'HELP (19D copy)', 'HELPFS': 'full-screen HELP',
}


def cp_tables():
    lines, decks = apply_updates(CPSRC, 'DMKCFC')
    cmds, qry, setl = [], [], []
    mode = None
    for l in lines:
        if l.startswith('*'):
            continue
        f = l.split()
        if not f:
            continue
        if l.startswith('QRYLIST'):
            mode = 'Q'
        elif l.startswith('SETLIST'):
            mode = 'S'
        elif l.startswith('QRYLAST') or l.startswith('QRYCLASB'):
            mode = None
        m = re.search(r'COMND\s+([^,\s]+),([^,]+),(\d+),([^,\s]+)', l)
        if m and not l.startswith('&'):
            cmds.append((m.group(1), classes(m.group(2)), int(m.group(3)),
                         m.group(4)))
            continue
        m = re.search(r"DC\s+C'(.{8})',AL1\((\d+),([^,]+),(\d+),(\d+)\)", l)
        if m and mode:
            row = (m.group(1).strip(), int(m.group(2)), classes(m.group(3)),
                   int(m.group(4)), int(m.group(5)))
            (qry if mode == 'Q' else setl).append(row)
            if l.startswith('SETLAST'):
                mode = None
    return cmds, qry, setl, decks


def cms_nucleus():
    out = []
    for l in open(CMSSRC, encoding='latin-1'):
        m = re.match(r'\s*JFUN\s+([A-Z0-9$#@]+)(?:,([A-Z0-9$#@]+))?', l[:72])
        if m and not m.group(1).startswith('DMS'):
            out.append((m.group(1), m.group(2) or m.group(1)))
    return sorted(set(out))


def main():
    cmds, qry, setl, decks = cp_tables()
    o = []
    w = o.append
    w('# 50 -- CP and CMS command tables')
    w('')
    w('Generated by `arch/31bit/tools/cmdtables.py`; do not edit by hand. '
      '**+** marks a VM/370plus addition or change.')
    w('')
    w('## CP commands')
    w('')
    w('From the `COMND` table in DMKCFC (CE source plus %s), in table order '
      '(CP searches it in this order, so an abbreviation goes to the first '
      'match). *Abbrev* is the shortest accepted form; *Class* is the '
      'privilege class (any = no class needed, also before LOGON).'
      % (', '.join(decks) or 'no decks'))
    w('')
    w('| Command | Abbrev | Class | Routine | Function |')
    w('|---|---|---|---|---|')
    for n, c, a, r in cmds:
        d = CPDESC.get(n, '')
        if n in CPPLUS:
            d += '; ' + CPPLUS[n]
        w('| %s | %s | %s | %s | %s |' % (n, n[:a], c, r if r != '0' else '(DMKCFC)', d))
    w('')
    w('### QUERY operands')
    w('')
    w('From QRYLIST. The same word appears twice when classes B and G get '
      'different answers (B: the real device, G: the virtual one).')
    w('')
    w('| Operand | Abbrev | Class | Module | Note |')
    w('|---|---|---|---|---|')
    for n, t, c, m, i in qry:
        w('| %s | %s | %s | %s | %s |' % (n, n[:t], c, QMOD.get(m, m), QPLUS.get(n, '')))
    w('')
    w('### SET operands')
    w('')
    w('| Operand | Abbrev | Class | Module | Note |')
    w('|---|---|---|---|---|')
    for n, t, c, m, i in setl:
        w('| %s | %s | %s | %s | %s |' % (n, n[:t], c, SMOD.get(m, m), SPLUS.get(n, '')))
    w('')
    w('## CMS commands')
    w('')
    w('### In the nucleus')
    w('')
    w('From the JFUN table in DMSFNC (internal DMSxxx entries left out). '
      'Always available, no disk needed.')
    w('')
    w('| Command | Entry | Function |')
    w('|---|---|---|')
    for n, e in cms_nucleus():
        w('| %s | %s | %s |' % (n, e, CMSDESC.get(n, '')))
    w('')
    disks = {}
    for l in open(DISKS):
        f = l.split()
        disks.setdefault((f[2][0], f[1]), []).append(f[0])
    names = {'S': 'S (190, the CMS system disk)',
             'U': 'U (MAINT 19D, VM/370plus additions)',
             'Y': 'Y (19E, CE tools and languages)'}
    for d in 'SUY':
        for t in ('MODULE', 'EXEC'):
            fl = sorted(disks.get((d, t), []))
            if not fl:
                continue
            w('### %s files on %s' % (t, names[d]))
            w('')
            desc = [x for x in fl if x in CMSDESC]
            rest = [x for x in fl if x not in CMSDESC]
            if desc:
                w('| Command | Function |')
                w('|---|---|')
                for x in desc:
                    w('| %s | %s |' % (x, CMSDESC[x]))
                w('')
            if rest:
                w(('Also: ' if desc else '') + ', '.join(rest) + '.')
                w('')
    w('## Not yet there (z/VM names, see the plan in 30-STATE)')
    w('')
    w('CP: DEFINE CPU / NIC / LAN / VSWITCH / MDISK, QUERY FRAMES, '
      'QUERY NSS, IUCV. CMS: XEDIT (THE), FILELIST (FULIST), RDRLIST, '
      'NOTE / TELL, GLOBALV, PIPE, NUCXLOAD.')
    open(OUT, 'w').write('\n'.join(o) + '\n')
    print('%s: %d CP commands, %d QUERY, %d SET operands' %
          (OUT, len(cmds), len(qry), len(setl)))


if __name__ == '__main__':
    sys.exit(main())
