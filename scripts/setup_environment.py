"""Create the shared project environment without building an EXE."""
from pathlib import Path
import subprocess,sys
root=Path(__file__).resolve().parents[1]
python=root/'.venv'/('Scripts/python.exe' if sys.platform=='win32' else 'bin/python')
if not python.exists():subprocess.run([sys.executable,'-m','venv',str(root/'.venv')],check=True)
subprocess.run([str(python),'-m','pip','install','-r',str(root/'requirements.txt')],check=True)
print('Environment ready')
