"""Run unit checks, or include complete game and voice checks with --full."""
import argparse
from pathlib import Path
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parent

def main():
    parser=argparse.ArgumentParser(description='Check Alem AI')
    parser.add_argument('--full',action='store_true',help='Also exercise all scenarios and the voice bank')
    args=parser.parse_args()
    suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'))
    if not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful():return 1
    if args.full:
        for module in ('checks.verify_training','checks.verify_voice'):
            subprocess.run([sys.executable,'-m',module],cwd=ROOT,check=True)
    return 0

if __name__=='__main__':raise SystemExit(main())
