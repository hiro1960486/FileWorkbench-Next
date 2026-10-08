"""Windows向け名前検証と、上書きしないリネーム・復元。"""
import os
import re
import json
from pathlib import Path
from datetime import datetime

def key(path):
    return str(Path(path).absolute()).casefold()

def validate_name(name):
    if not name or name in ('.', '..') or name.endswith((' ', '.')):
        raise ValueError('空の名前・末尾の空白／ピリオドは使用できません')
    if re.search(r'[<>:"/\\|?*\x00-\x1f]', name):
        raise ValueError('Windowsで使用できない文字が含まれています')
    if name.split('.')[0].upper() in {'CON','PRN','AUX','NUL',*[f'COM{i}' for i in range(1,10)],*[f'LPT{i}' for i in range(1,10)]}:
        raise ValueError('Windowsの予約名は使用できません')
    if len(name.encode('utf-16-le')) // 2 > 255:
        raise ValueError('名前が長すぎます')

def unique_planned(path, reserved):
    path = Path(path)
    candidate = path
    i = 1
    while candidate.exists() or key(candidate) in reserved:
        candidate = path.with_name(f'{path.stem}_{i}{path.suffix}')
        i += 1
    return candidate

def no_replace(src, dst):
    """Windowsのrenameは既存先を上書きしない。他OSではhardlinkで排他確保。"""
    src, dst = Path(src), Path(dst)
    if os.name == 'nt':
        if key(src) == key(dst) and str(src) != str(dst):
            import uuid
            temp = src.with_name('.fwn_' + uuid.uuid4().hex + src.suffix)
            src.rename(temp)
            try:
                temp.rename(dst)
            except Exception:
                temp.rename(src)
                raise
        else:
            src.rename(dst)
    else:
        os.link(src, dst)
        try:
            src.unlink()
        except Exception:
            dst.unlink()
            raise

def identity(path):
    s = Path(path).stat()
    return [s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns]

def restore(entries):
    remaining, errors = [], []
    for entry in reversed(entries):
        try:
            if identity(entry['current']) != entry['identity']:
                raise ValueError('変更後のファイルが更新／置換されています')
            no_replace(entry['current'], entry['original'])
        except Exception as exc:
            remaining.append(entry)
            errors.append(f"{entry['current']} → {entry['original']}: {exc}")
    return list(reversed(remaining)), errors

def journal_path():
    base = Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'FileWorkbench_Next'
    base.mkdir(parents=True, exist_ok=True)
    return base / 'rename_history.json'

def save_history(history):
    target = journal_path()
    temp = target.with_suffix('.tmp')
    temp.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding='utf-8')
    os.replace(temp, target)

def load_history():
    p = journal_path()
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else []

def write_log(operation, source, target, status, error):
    import csv
    path = journal_path().parent / 'operations.csv'
    exists = path.exists()
    with path.open('a', newline='', encoding='utf-8-sig') as out:
        writer = csv.writer(out)
        if not exists:
            writer.writerow(['time', 'operation', 'source', 'target', 'status', 'error'])
        writer.writerow([datetime.now().isoformat(timespec='seconds'), operation, source, target, status, error])
