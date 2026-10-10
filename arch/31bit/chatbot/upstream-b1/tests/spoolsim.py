"""PC-side stand-in for the CHATBOT EXEC: turns (sender, text) pairs into request
files, runs the compiled bot under rxvm exactly as the EXEC would on CMS, and
returns the reply files.  Reader/punch are directories."""
import os, subprocess, shutil, glob, sys

class Sim:
    def __init__(self, work, data, rxbin, rxvm, lib, config=None, fresh=True):
        self.work = work.rstrip('/') + '/'
        self.rxbin, self.rxvm, self.lib = rxbin, rxvm, lib
        if fresh and os.path.isdir(work):
            shutil.rmtree(work)
        os.makedirs(work, exist_ok=True)
        for f in glob.glob(os.path.join(data, '*')):
            shutil.copy(f, work)
        with open(self.work + 'CHATBOT.CONFIG', 'w') as f:
            f.write('\n'.join(config or ['SEED 7', 'CRISIS YES', 'WIDTH 72']) + '\n')
        self.seq = 0

    def run(self, requests, extra=None):
        """requests: list of (sender, text).  returns list of reply texts (lines joined)."""
        names = []
        for sender, text in requests:
            self.seq += 1
            fn = 'Q%04d' % self.seq
            names.append(fn)
            with open(self.work + fn + '.CBREQ', 'w') as f:
                f.write(':READ %s CBREQ A\n' % fn if False else '')
                f.write('FROM %s\n' % sender)
                for line in text.split('\n'):
                    f.write(line + '\n')
        with open(self.work + 'CHATBOT.CBQUEUE', 'w') as f:
            f.write('\n'.join(names) + '\n')
        cmd = [self.rxvm, self.lib, self.rxbin, '-a', self.work] + (extra or [])
        p = subprocess.run(cmd, capture_output=True, text=True)
        if p.returncode != 0 or p.stderr.strip():
            sys.stderr.write('rxvm rc=%s\n%s\n%s\n' % (p.returncode, p.stdout, p.stderr))
        out = []
        for fn in names:
            path = self.work + fn + '.CBRPL'
            out.append(open(path).read().rstrip('\n') if os.path.exists(path) else None)
        self.stdout = p.stdout
        return out
