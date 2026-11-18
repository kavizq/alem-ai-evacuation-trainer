"""Create an isolated local environment and launch the game."""
from pathlib import Path
import os
import subprocess
import sys
import venv

root=Path(__file__).resolve().parent
python=root/'.venv'/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
if not python.exists():
    print('Creating a local Python environment...')
    venv.create(root/'.venv',with_pip=True)
check=subprocess.run([str(python),'-c','import panda3d; assert panda3d.__version__ == "1.10.16"'],capture_output=True)
if check.returncode:
    subprocess.run([str(python),'-m','pip','install','-r',str(root/'requirements.txt')],check=True)
raise SystemExit(subprocess.call([str(python),str(root/'main.py'),*sys.argv[1:]],cwd=root))
