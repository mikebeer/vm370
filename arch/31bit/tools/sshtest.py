import sys,time,re,paramiko
log=sys.argv[1]
for i in range(300):
    try:
        if 'ifconfig' in open(log,errors='replace').read(): break
    except FileNotFoundError: pass
    time.sleep(3)
time.sleep(5)
for attempt in range(6):
    try:
        c=paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        t0=time.time()
        c.connect('10.1.1.2',username='root',password='vm370plus',timeout=60,banner_timeout=120,auth_timeout=120,look_for_keys=False,allow_agent=False)
        print('connected in %.1fs'%(time.time()-t0))
        for cmd in ['uname -a','id','free','echo hello from ssh > /tmp/s; cat /tmp/s',"awk 'BEGIN{print sqrt(2)}'"]:
            i,o,e=c.exec_command(cmd,timeout=60); print('$',cmd); print(o.read().decode(),e.read().decode(),end='')
        c.close(); break
    except Exception as ex:
        print('attempt',attempt,repr(ex)); time.sleep(10)
