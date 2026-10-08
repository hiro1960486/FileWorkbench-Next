"""Reusable, Qt-independent file operations with exclusive destinations and recovery data."""
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Protocol
from datetime import datetime, timedelta
import hashlib, json, os, shutil, threading, uuid

@dataclass
class OperationResult:
    operation: str
    source: str
    target: str = ''
    status: str = '成功'
    error: str = ''
    history_id: str = ''

class FileOperationsPort(Protocol):
    def perform(self, operation, paths, destination=None, cancel=lambda:False): ...
    def history(self): ...
    def rename_many(self,plans,cancel=lambda:False): ...
    def restore_backup(self, history_id, destination=None, collision='rename'): ...


def data_directory():
    return Path(os.environ.get('LOCALAPPDATA',str(Path.home()))) / 'FileWorkbench_Next'


def fingerprint(path):
    path=Path(path)
    if path.is_symlink() or (hasattr(path,'is_junction') and path.is_junction()):raise ValueError('リンクは安全のため処理対象外です')
    if path.is_file():
        h=hashlib.sha256()
        with path.open('rb') as f:
            for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
        return {'type':'file','size':path.stat().st_size,'sha256':h.hexdigest()}
    if not path.is_dir():raise FileNotFoundError(path)
    result={'type':'folder','entries':{}}
    for p in sorted(path.rglob('*')):
        if p.is_symlink() or (hasattr(p,'is_junction') and p.is_junction()):raise ValueError('リンクを含むフォルダーは処理対象外です')
        result['entries'][p.relative_to(path).as_posix()]=fingerprint(p) if p.is_file() else {'type':'folder'}
    return result


def unique_destination(path):
    path=Path(path);i=1;candidate=path
    while candidate.exists():
        candidate=path.with_name(f'{path.stem}_{i}{path.suffix}');i+=1
    return candidate


def normalize_selection(paths):
    # Avoid processing a directory and one of its children twice.
    values=list(dict.fromkeys(Path(p).absolute() for p in paths))
    return [p for p in values if not any(q!=p and q in p.parents for q in values)]


def copy_exclusive(source,target):
    source,target=Path(source),Path(target)
    if source.is_symlink() or (hasattr(source,'is_junction') and source.is_junction()):raise ValueError('リンクは処理対象外です')
    if source.is_dir():
        target.mkdir()  # exclusive allocation; never overwrite
        for child in source.iterdir():copy_exclusive(child,target/child.name)
    else:
        with source.open('rb') as inp,target.open('xb') as out:shutil.copyfileobj(inp,out,1024*1024)
        shutil.copystat(source,target)


class FileOperationsService:
    def __init__(self,root=None,trash_backend=None):
        self.root=Path(root) if root else data_directory()
        self.root.mkdir(parents=True,exist_ok=True);self.lock=threading.RLock()
        if trash_backend is None:
            from send2trash import send2trash
            trash_backend=send2trash
        self.trash_backend=trash_backend

    def history(self):
        path=self.root/'recovery_history.json'
        return json.loads(path.read_text(encoding='utf-8')) if path.exists() else []

    def _save(self,entries):
        path=self.root/'recovery_history.json';temp=path.with_suffix('.tmp')
        temp.write_text(json.dumps(entries,ensure_ascii=False,indent=2),encoding='utf-8');os.replace(temp,path)

    def _record(self,result):
        import csv
        path=self.root/'operations.csv'
        with path.open('a',newline='',encoding='utf-8-sig') as out:
            writer=csv.writer(out)
            if out.tell()==0:writer.writerow(['time','operation','source','target','status','error','history_id'])
            writer.writerow([datetime.now().isoformat(timespec='seconds'),*asdict(result).values()])

    def _backup(self,path,operation):
        ident=uuid.uuid4().hex;folder=self.root/'backups'/ident;folder.mkdir(parents=True)
        target=folder/path.name;before=fingerprint(path);copy_exclusive(path,target)
        if fingerprint(target)!=before or fingerprint(path)!=before:
            raise ValueError('退避照合に失敗しました。元データは変更していません')
        entry={'id':ident,'source':str(path),'backup':str(target),'fingerprint':before,
               'operation':operation,'state':'退避済み','protected':True,
               'created':datetime.now().isoformat(timespec='seconds'),
               'retention_until':(datetime.now()+timedelta(days=30)).isoformat(timespec='seconds')}
        entries=self.history();entries.append(entry);self._save(entries);return entry

    def _update(self,entry,**values):
        entries=self.history()
        for e in entries:
            if e['id']==entry['id']:e.update(values)
        self._save(entries)

    def perform(self,operation,paths,destination=None,cancel=lambda:False):
        if operation not in ('copy','move','duplicate','trash'):raise ValueError(operation)
        results=[]
        with self.lock:
            for path in normalize_selection(paths):
                if cancel():break
                result=OperationResult(operation,str(path))
                try:
                    if not path.exists():raise FileNotFoundError(path)
                    if path.is_symlink() or (hasattr(path,'is_junction') and path.is_junction()):raise ValueError('リンクは処理対象外です')
                    if operation in ('copy','move'):
                        directory=Path(destination).absolute() if destination else None
                        if directory is None or not directory.is_dir():raise ValueError('出力先フォルダーを指定してください')
                        if path.is_dir() and (directory==path or path in directory.parents):raise ValueError('対象自身やその配下へは保存できません')
                    else:directory=path.parent
                    if operation=='trash':
                        backup=self._backup(path,operation);result.history_id=backup['id']
                        if fingerprint(path)!=backup['fingerprint']:raise ValueError('元データが変更されたため中止しました')
                        self.trash_backend(str(path))
                        if path.exists():raise RuntimeError('ごみ箱への移動を確認できません')
                        self._update(backup,state='ごみ箱へ移動済み')
                    else:
                        target=unique_destination(directory/path.name);result.target=str(target)
                        backup=self._backup(path,operation) if operation=='move' else None
                        if backup:result.history_id=backup['id']
                        before=fingerprint(path);copy_exclusive(path,target)
                        if fingerprint(target)!=before or fingerprint(path)!=before:raise ValueError('内容照合失敗。元データを残しました')
                        if operation=='move':
                            # Recycle the source instead of permanent unlink; backup is retained.
                            self.trash_backend(str(path))
                            if path.exists():raise RuntimeError('元データのごみ箱移動を確認できません')
                            self._update(backup,state='移動済み',target=str(target))
                except Exception as exc:result.status='失敗';result.error=str(exc)
                self._record(result);results.append(result)
        return results

    def rename_many(self,plans,cancel=lambda:False):
        from ..core.safety import no_replace,validate_name
        results=[]
        with self.lock:
            for source,target in plans:
                if cancel():break
                source,target=Path(source),Path(target);result=OperationResult('rename',str(source),str(target))
                try:
                    if source.parent!=target.parent:raise ValueError('名前変更は同じフォルダー内で行います')
                    validate_name(target.name);backup=self._backup(source,'rename');result.history_id=backup['id']
                    if fingerprint(source)!=backup['fingerprint']:raise ValueError('元データが変更されたため中止')
                    no_replace(source,target);self._update(backup,state='リネーム済み',target=str(target))
                except Exception as exc:result.status='失敗';result.error=str(exc)
                self._record(result);results.append(result)
        return results

    def restore_backup(self,history_id,destination=None,collision='rename'):
        with self.lock:
            entry=next(e for e in self.history() if e['id']==history_id)
            backup=Path(entry['backup']);source=Path(entry['source'])
            if fingerprint(backup)!=entry['fingerprint']:raise ValueError('退避データの照合失敗。復元しません')
            folder=Path(destination) if destination else source.parent
            if not folder.is_dir():raise ValueError('復元先フォルダーが存在しません。任意復元先を指定してください')
            target=folder/source.name
            if target.exists():
                if collision=='skip':return OperationResult('restore',str(backup),str(target),'スキップ')
                target=unique_destination(target)
            copy_exclusive(backup,target)
            if fingerprint(target)!=entry['fingerprint']:raise ValueError('復元後の照合失敗。退避データは保持しています')
            self._update(entry,restored_to=str(target),restored_at=datetime.now().isoformat(timespec='seconds'))
            result=OperationResult('restore',str(backup),str(target),history_id=history_id)
            self._record(result);return result

_default=None
def default_service():
    global _default
    if _default is None:_default=FileOperationsService()
    return _default

# The service intentionally never purges recovery copies automatically.
