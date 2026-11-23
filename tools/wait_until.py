#!/usr/bin/env python3
"""Wait until a Seoul (KST) clock time, in chunks that fit a 10-minute command limit.
Usage: python3 tools/wait_until.py 17:00
Sleeps at most 540 s per call. Exit 0 = the time has come; exit 1 = still waiting (run again)."""
import sys, time, datetime as dt
KST = dt.timezone(dt.timedelta(hours=9))
h, m = map(int, sys.argv[1].split(':'))
now = dt.datetime.now(KST)
target = now.replace(hour=h, minute=m, second=0, microsecond=0)
left = (target - now).total_seconds()
if left <= 0:
    print('time reached', now.strftime('%H:%M:%S')); sys.exit(0)
time.sleep(min(left, 540))
left = (target - dt.datetime.now(KST)).total_seconds()
print(f'remaining {max(0, int(left))}s'); sys.exit(0 if left <= 0 else 1)
