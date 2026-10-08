"""Package the current Windows executable with documentation and hashes."""
from pathlib import Path
import hashlib,zipfile
ROOT=Path(__file__).resolve().parents[1]
VERSION='3.3_RC'

def package(root=ROOT):
    root=Path(root);exe=root/'dist/FileWorkbench_Next.exe'
    if not exe.is_file():raise FileNotFoundError(exe)
    release=root/'release';release.mkdir(exist_ok=True)
    archive=release/f'FileWorkbench_Next_{VERSION}_Windows_x64.zip'
    checksum=hashlib.sha256(exe.read_bytes()).hexdigest()+'  FileWorkbench_Next.exe\n'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        z.write(exe,exe.name);z.writestr('SHA256_EXE.txt',checksum)
        for name in ('README.txt','LICENSE.txt'):
            z.write(root/name,name)
        for p in sorted((root/'docs').rglob('*')):
            if p.is_file():z.write(p,p.relative_to(root))
    (release/'SHA256_RELEASE.txt').write_text(hashlib.sha256(archive.read_bytes()).hexdigest()+'  '+archive.name+'\n')
    return archive
if __name__=='__main__':print(package())
