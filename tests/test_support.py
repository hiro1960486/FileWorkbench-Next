"""Keep automated tests away from the user's real settings and recovery history."""
import os,tempfile,atexit,errno
from pathlib import Path
_root=None
def isolate_test_environment():
    global _root
    if _root is not None:return
    _root=tempfile.TemporaryDirectory(prefix='fwn_tests_');atexit.register(_root.cleanup)
    os.environ['LOCALAPPDATA']=str(Path(_root.name)/'appdata')
    os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
    from PySide6.QtCore import QSettings
    QSettings.setDefaultFormat(QSettings.IniFormat)
    QSettings.setPath(QSettings.IniFormat,QSettings.UserScope,str(Path(_root.name)/'settings'))
    QSettings.setPath(QSettings.IniFormat,QSettings.SystemScope,str(Path(_root.name)/'system_settings'))

def make_test_symlink(testcase,link,target,**kwargs):
    """Create a link fixture or skip only when the OS denies link creation."""
    try:
        link.symlink_to(target,**kwargs)
    except NotImplementedError as exc:
        testcase.skipTest(f'この環境ではシンボリックリンクを作成できません: {exc}')
    except OSError as exc:
        unavailable={errno.EPERM,errno.EACCES,errno.ENOSYS}
        unavailable.update(x for x in (getattr(errno,'ENOTSUP',None),getattr(errno,'EOPNOTSUPP',None)) if x is not None)
        if getattr(exc,'winerror',None)==1314 or exc.errno in unavailable:
            testcase.skipTest(f'この環境ではシンボリックリンクを作成できません: {exc}')
        raise
