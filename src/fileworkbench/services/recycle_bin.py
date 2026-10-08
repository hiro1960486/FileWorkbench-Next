"""Windows Shell adapter. Recycle Bin metadata files are never directly modified."""
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
import sys,time,tempfile,threading
from .file_operations import unique_destination,copy_exclusive,fingerprint,OperationResult

@dataclass
class RecycleEntry:
    item_id:str
    name:str
    original_directory:str
    deleted_at:str
    is_folder:bool

class RecycleBinPort(Protocol):
    def list_entries(self): ...
    def restore(self,item_id,destination=None,collision='rename'): ...

class WindowsRecycleBin:
    def __init__(self):self._local=threading.local()
    def _finish(self):
        if getattr(self._local,'initialized',False):
            import pythoncom
            pythoncom.CoUninitialize();self._local.initialized=False
    def list_entries(self):
        try:return self._list_entries()
        finally:self._finish()
    def restore(self,item_id,destination=None,collision='rename'):
        try:return self._restore(item_id,destination,collision)
        finally:self._finish()
    def _shell(self):
        if sys.platform!='win32':raise RuntimeError('Windowsのごみ箱はWindows上で利用できます')
        import pythoncom,win32com.client
        pythoncom.CoInitialize();self._local.initialized=True
        return win32com.client.Dispatch('Shell.Application')

    def _list_entries(self):
        shell=self._shell();folder=shell.NameSpace(10)
        if folder is None:raise RuntimeError('ごみ箱を開けません')
        return [RecycleEntry(str(item.Path),str(item.Name),str(item.ExtendedProperty('System.Recycle.DeletedFrom') or ''),
                            str(item.ExtendedProperty('System.Recycle.DateDeleted') or ''),bool(item.IsFolder))
                for item in folder.Items()]

    def _restore(self,item_id,destination=None,collision='rename'):
        shell=self._shell();items=shell.NameSpace(10).Items()
        item=next((x for x in items if str(x.Path)==item_id),None)
        if item is None:raise FileNotFoundError('ごみ箱項目が見つかりません。再検索してください')
        name=str(item.Name);original=str(item.ExtendedProperty('System.Recycle.DeletedFrom') or '')
        if Path(name).name!=name:raise ValueError('不正な項目名')
        folder=Path(destination or original)
        if not folder.is_dir():raise ValueError('復元先フォルダーを指定してください')
        target=folder/name
        if target.exists():
            if collision=='skip':return OperationResult('recycle_restore',item_id,str(target),'スキップ')
            target=unique_destination(target)
        # Shell restores to a unique staging directory. If anything fails, keep it intact.
        staging=Path(tempfile.mkdtemp(prefix='.fwn_restore_',dir=folder));staged=staging/name
        shell.NameSpace(str(staging)).MoveHere(item,0)
        deadline=time.monotonic()+60
        while time.monotonic()<deadline:
            still_present=any(str(x.Path)==item_id for x in shell.NameSpace(10).Items())
            if staged.exists() and not still_present:break
            time.sleep(.1)
        else:raise RuntimeError('Shell復元の完了を確認できません。退避場所: '+str(staging))
        try:
            signature=fingerprint(staged);copy_exclusive(staged,target)
            if fingerprint(target)!=signature:raise ValueError('復元後照合失敗')
            # Staged data remains as a recovery copy, never delete it silently.
            return OperationResult('recycle_restore',item_id,str(target),error='復元用退避: '+str(staging))
        except Exception as exc:raise RuntimeError(str(exc)+' / 復元用退避: '+str(staging)) from exc
