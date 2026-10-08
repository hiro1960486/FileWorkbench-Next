"""Build from the project root; retain complete subprocess output in build.log."""
import os,sys,struct,subprocess,json
from pathlib import Path
from datetime import datetime
ROOT=Path(__file__).resolve().parents[1]

def pyinstaller_arguments(python,root=ROOT):
    root=Path(root)
    args=[str(python),'-m','PyInstaller','--noconsole','--onefile','--clean','--noconfirm',
          '--distpath',str(root/'dist'),'--workpath',str(root/'build'),
          '--specpath',str(root/'build'),'--name','FileWorkbench_Next',
          '--paths',str(root/'src'),'--icon',str(root/'assets/app.ico'),
          '--hidden-import','win32timezone','--collect-submodules','fileworkbench','--collect-data','send2trash',
          '--add-data',str(root/'assets')+';assets',
          '--add-data',str(root/'docs')+';docs']
    for manifest in sorted((root/'src/fileworkbench/modules').glob('*/module.json')):
        args.extend(['--add-data',str(manifest)+';fileworkbench/modules/'+manifest.parent.name])
    return args+[str(root/'app_main.py')]

def build():
    with (ROOT/'build.log').open('w',encoding='utf-8') as log:
        def say(text):print(text,flush=True);log.write(text+'\n');log.flush()
        def run(args):
            say('COMMAND: '+subprocess.list2cmdline([str(a) for a in args]))
            env=os.environ.copy();env['PYTHONPATH']=str(ROOT/'src');env['QT_QPA_PLATFORM']='offscreen';env['PYTHONIOENCODING']='utf-8'
            with subprocess.Popen([str(a) for a in args],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,env=env) as process:
                for line in process.stdout:say(line.decode('utf-8',errors='replace').rstrip())
                if process.wait():raise RuntimeError('Command failed; see build.log')
        try:
            say('FileWorkbench Next 3.3 RC '+datetime.now().isoformat())
            if sys.platform!='win32' or struct.calcsize('P')!=8:raise RuntimeError('Windows 64-bit Python is required')
            python=ROOT/'.venv/Scripts/python.exe'
            if not python.exists():run([sys.executable,'-m','venv',ROOT/'.venv'])
            run([python,'-m','pip','install','-r',ROOT/'requirements.txt'])
            run([python,'-m','compileall','-q',ROOT/'src',ROOT/'scripts'])
            run([python,'-m','unittest','discover','-s','tests','-p','test_module*.py','-v'])
            (ROOT/'build').mkdir(exist_ok=True)
            run(pyinstaller_arguments(python))
            # Verify the frozen EXE, rather than assuming packaging implies startup success.
            smoke=ROOT/'build/exe-smoke.json'
            smoke.unlink(missing_ok=True)
            env=os.environ.copy();env['QT_QPA_PLATFORM']='offscreen'
            subprocess.run([str(ROOT/'dist/FileWorkbench_Next.exe'),'--smoke-test',str(smoke)],cwd=ROOT,env=env,check=True,timeout=90)
            report=json.loads(smoke.read_text(encoding='utf-8'))
            if report.get('drop_error') or report.get('recycle_error') or report.get('unavailable') or report.get('missing_resources') or report.get('missing_modules'):
                raise RuntimeError('Frozen EXE validation failed: '+str(report))
            (ROOT/'release').mkdir(exist_ok=True)
            (ROOT/'release/exe-smoke.json').write_text(smoke.read_text(encoding='utf-8'),encoding='utf-8')
            run([python,ROOT/'scripts/package_release.py'])
            say('SUCCESS: dist/FileWorkbench_Next.exe and release/FileWorkbench_Next_3.3_RC_Windows_x64.zip')
            return 0
        except Exception as exc:say('ERROR: '+str(exc));return 1
if __name__=='__main__':sys.exit(build())
