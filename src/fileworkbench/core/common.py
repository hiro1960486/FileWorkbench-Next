from pathlib import Path
import hashlib, os, subprocess, sys
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFileDialog, QMessageBox

def resource_path(name):
    return Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parents[3])) / name

def app_icon(): return QIcon(str(resource_path('assets/app.ico')))

def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024), b''): h.update(chunk)
    return h.hexdigest()

def open_default(path):
    try:
        if sys.platform.startswith('win'): os.startfile(str(path))
        else: subprocess.Popen(['xdg-open',str(path)])
    except Exception as exc: QMessageBox.warning(None,'起動エラー',str(exc))

def choose_folder(parent,title='フォルダーを選択'):
    value=QFileDialog.getExistingDirectory(parent,title)
    return Path(value) if value else None
