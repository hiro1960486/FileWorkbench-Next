"""Reusable Qt input, selection, menus, and background operation presentation."""
from pathlib import Path
import os,subprocess,threading
from PySide6.QtCore import Qt,Signal,QObject,QEvent,QThread
from PySide6.QtWidgets import *
from ..interfaces.contracts import ModuleContext
from ..services.file_operations import default_service
from ..core.common import open_default,digest

class PathEdit(QLineEdit):
    path_dropped=Signal(str)
    paths_dropped=Signal(list)
    def __init__(self,folder_only=False,parent=None):
        super().__init__(parent);self.folder_only=folder_only;self.setAcceptDrops(True)
        self.setPlaceholderText('ここへドラッグ＆ドロップ、または選択')
    def mousePressEvent(self,event):
        self.drag_start=event.position().toPoint();super().mousePressEvent(event)
    def mouseMoveEvent(self,event):
        from PySide6.QtCore import QMimeData,QUrl
        from PySide6.QtGui import QDrag
        if event.buttons() & Qt.LeftButton and hasattr(self,'drag_start') and (event.position().toPoint()-self.drag_start).manhattanLength()>=QApplication.startDragDistance() and Path(self.text()).exists():
            mime=QMimeData();mime.setUrls([QUrl.fromLocalFile(self.text())]);drag=QDrag(self);drag.setMimeData(mime);drag.exec(Qt.CopyAction);return
        super().mouseMoveEvent(event)
    def local_paths(self,event):
        return [Path(u.toLocalFile()) for u in event.mimeData().urls() if u.isLocalFile()]
    def dragEnterEvent(self,event):
        if self.local_paths(event):event.acceptProposedAction()
        else:event.ignore()
    def dragMoveEvent(self,event):
        # QLineEdit's default drag-move handling targets text; keep file URLs here.
        if self.local_paths(event):event.acceptProposedAction()
        else:event.ignore()
    def dropEvent(self,event):
        values=self.local_paths(event)
        if not values:event.ignore();return
        # Own this drop even when invalid, so it cannot turn into a parent input drop.
        event.acceptProposedAction()
        if self.folder_only and not values[0].is_dir():
            QMessageBox.warning(self,'フォルダーを指定','この欄にはフォルダーをドロップしてください。入力内容は変更していません。')
            return
        if not all(p.exists() for p in values):
            QMessageBox.warning(self,'対象がありません','存在するファイル／フォルダーをドロップしてください。')
            return
        self.setText(str(values[0]));self.path_dropped.emit(str(values[0]));self.paths_dropped.emit([str(p) for p in values])

class Job(QThread):
    result_ready=Signal(object);failed=Signal(str)
    def __init__(self,function,parent=None):super().__init__(parent);self.function=function;self.cancel=threading.Event()
    def run(self):
        try:self.result_ready.emit(self.function(self.cancel.is_set))
        except Exception as exc:self.failed.emit(str(exc))

def run_job(parent,label,function):
    """Keep the UI responsive; cancellation takes effect between items."""
    job=Job(function,parent);dialog=QProgressDialog(label+'\n停止は現在の項目処理後に反映されます','停止',0,0,parent)
    dialog.setWindowModality(Qt.ApplicationModal);dialog.setMinimumDuration(0)
    state={'result':None,'error':''}
    job.result_ready.connect(lambda value:state.update(result=value))
    job.failed.connect(lambda value:state.update(error=value))
    dialog.canceled.connect(job.cancel.set);job.finished.connect(dialog.close)
    parent.setProperty('operation_busy',True)
    job.start();dialog.show()
    while job.isRunning():
        QApplication.processEvents();job.wait(15)
    QApplication.processEvents();dialog.close();parent.setProperty('last_job_cancelled',job.cancel.is_set());job.deleteLater();parent.setProperty('operation_busy',False)
    if state['error']:raise RuntimeError(state['error'])
    return state['result']

class ModuleWidget(QWidget):
    """Every module UI explicitly binds its input and action boundary to a ModulePort."""
    def __init__(self):
        super().__init__();self.setAcceptDrops(True);self.port=None;self.status=QLabel('対象を選択してください')
        self.status.setWordWrap(True);self.service=default_service()
    def bind_port(self,port):self.port=port
    def closeEvent(self,event):
        if self.property('operation_busy'):event.ignore();return
        super().closeEvent(event)
    def input_paths(self,paths):
        if self.property('operation_busy'):return
        if not self.port:
            self.status.setText('単体起動はrun_module.batを使用してください');return
        self.port.emit('target.individual_requested',{})
        try:self.port.receive_context(ModuleContext(selected_paths=list(paths),source_module='drop'))
        except Exception as exc:QMessageBox.warning(self,'入力エラー',str(exc))
    def dragEnterEvent(self,event):
        if event.mimeData().hasUrls() and any(u.isLocalFile() for u in event.mimeData().urls()):event.acceptProposedAction()
    def dragMoveEvent(self,event):
        if any(u.isLocalFile() for u in event.mimeData().urls()):event.acceptProposedAction()
        else:event.ignore()
    def dropEvent(self,event):
        paths=[u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
        if paths:self.input_paths(paths);event.acceptProposedAction()
    def eventFilter(self,obj,event):
        if event.type() in (QEvent.DragEnter,QEvent.DragMove) and any(u.isLocalFile() for u in event.mimeData().urls()):event.acceptProposedAction();return True
        if event.type()==QEvent.Drop:
            paths=[u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
            if paths:self.input_paths(paths);event.acceptProposedAction();return True
        return super().eventFilter(obj,event)
    def register_view(self,view,get_paths,extra_actions=()):
        view.setAcceptDrops(True);target=view.viewport() if isinstance(view,QAbstractScrollArea) else view
        target.setAcceptDrops(True);target.installEventFilter(self)
        if isinstance(view,QAbstractItemView):
            view.setDragEnabled(True);view.setSelectionMode(QAbstractItemView.ExtendedSelection);view.setSelectionBehavior(QAbstractItemView.SelectRows)
            view.setEditTriggers(QAbstractItemView.NoEditTriggers)
            view.header().setSectionResizeMode(QHeaderView.Interactive) if isinstance(view,QTreeWidget) else view.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
            view.header().setStretchLastSection(False) if isinstance(view,QTreeWidget) else view.horizontalHeader().setStretchLastSection(False)
        view.setContextMenuPolicy(Qt.CustomContextMenu)
        view.customContextMenuRequested.connect(lambda pos:self.show_actions(view,pos,get_paths,extra_actions))
    def show_actions(self,view,pos,get_paths,extra_actions=()):
        paths=list(dict.fromkeys(str(p) for p in get_paths() if p))
        menu=QMenu(self)
        actions={}
        for text,key in [('プレビュー','preview'),('名前の変更画面へ','rename'),('情報を表示','info'),('既定アプリで開く','open'),('保存場所を開く','reveal'),('フルパスをコピー','path'),('SHA256をコピー','hash')]:
            a=menu.addAction(text);a.setEnabled(bool(paths));actions[a]=key
        menu.addSeparator()
        for text,key in [('指定フォルダーへコピー…','copy'),('指定フォルダーへ移動…','move'),('同じ場所に複製','duplicate'),('ごみ箱へ移動…','trash')]:
            a=menu.addAction(text);a.setEnabled(bool(paths));actions[a]=key
        menu.addSeparator()
        for text,callback in extra_actions:
            a=menu.addAction(text);actions[a]=callback
        if isinstance(view,QAbstractItemView):
            a=menu.addAction('すべて選択');actions[a]=view.selectAll
            a=menu.addAction('選択を解除');actions[a]=view.clearSelection
        point=view.viewport().mapToGlobal(pos) if isinstance(view,QAbstractScrollArea) else view.mapToGlobal(pos)
        chosen=menu.exec(point);action=actions.get(chosen)
        if callable(action):action();return
        if not action or not paths:return
        try:
            if action=='preview':
                if self.port:self.port.emit('preview.requested',{'selected_paths':paths})
            elif action=='rename':
                if self.port:self.port.emit('rename.requested',{'selected_paths':paths})
            elif action=='info':
                lines=[]
                for value in paths[:100]:
                    path=Path(value);stat=path.stat();lines.append(f'{path}\n種類: {"フォルダー" if path.is_dir() else path.suffix or "ファイル"} / サイズ: {stat.st_size:,} bytes')
                QMessageBox.information(self,'選択項目の情報','\n\n'.join(lines))
            elif action=='open':open_default(Path(paths[0]))
            elif action=='reveal':
                if os.name=='nt':subprocess.Popen(['explorer.exe','/select,',paths[0]])
                else:open_default(Path(paths[0]).parent)
            elif action=='path':QApplication.clipboard().setText('\n'.join(paths))
            elif action=='hash':
                hashes=run_job(self,'SHA256を計算',lambda cancel:[f'{digest(p)}  {p}' for p in paths if Path(p).is_file() and not cancel()])
                QApplication.clipboard().setText('\n'.join(hashes))
            else:self.perform_action(action,paths)
        except Exception as exc:QMessageBox.warning(self,'操作エラー',str(exc))
    def perform_action(self,action,paths):
        destination=None
        if action in ('copy','move'):
            destination=QFileDialog.getExistingDirectory(self,'出力先フォルダー')
            if not destination:return
        detail='\n'.join(paths[:12])+ ('\n…' if len(paths)>12 else '')
        if action in ('move','trash'):
            text=f'{len(paths)}項目を処理します。\n{detail}\n\n出力先: {destination or "Windowsごみ箱"}\n退避データを作成・照合してから実行します。'
            if QMessageBox.question(self,'実行前の確認',text)!=QMessageBox.Yes:return
        if self.port:self.port.emit('files.will_change',{'selected_paths':paths,'operation':action})
        results=run_job(self,'ファイル処理',lambda cancel:self.service.perform(action,paths,destination,cancel))
        if self.port:self.port.emit('files.changed',{'results':[r.__dict__ for r in results]})
        lines=[f'{r.status}: {r.source}\n保存先: {r.target or "ごみ箱（退避履歴あり）"}\n{r.error}' for r in results]
        self.status.setText('\n'.join(lines) or '処理なし／停止')
        dialog=QDialog(self);dialog.setWindowTitle('処理結果・実際の保存先');layout=QVBoxLayout(dialog)
        text=QPlainTextEdit('\n\n'.join(lines));text.setReadOnly(True);layout.addWidget(text)
        buttons=QHBoxLayout();copy_result=QPushButton('結果をコピー');copy_result.clicked.connect(lambda:QApplication.clipboard().setText('\n\n'.join(lines)));open_target=QPushButton('保存場所を開く');targets=[Path(r.target) for r in results if r.target and Path(r.target).exists()];open_target.setEnabled(bool(targets));open_target.clicked.connect(lambda:open_default(targets[0] if targets[0].is_dir() else targets[0].parent));close=QPushButton('閉じる');close.clicked.connect(dialog.accept);buttons.addWidget(copy_result);buttons.addWidget(open_target);buttons.addStretch();buttons.addWidget(close);layout.addLayout(buttons);dialog.resize(760,420);dialog.exec()
    def selected_table_paths(self,table,columns=(0,)):
        values=[]
        for row in sorted({index.row() for index in table.selectionModel().selectedRows()}):
            for col in columns:
                item=table.item(row,col)
                if item:
                    path=item.data(Qt.UserRole) or item.text()
                    if Path(str(path)).exists():values.append(str(path))
        return values

class SortableItem(QTableWidgetItem):
    def __lt__(self,other):
        try:return float(self.text().replace(',',''))<float(other.text().replace(',',''))
        except ValueError:return self.text().casefold()<other.text().casefold()

class TreeItem(QTreeWidgetItem):
    def __lt__(self,other):
        column=self.treeWidget().sortColumn()
        if column==2:
            try:return int(self.text(column) or 0)<int(other.text(column) or 0)
            except ValueError:pass
        return self.text(column).casefold()<other.text(column).casefold()

class FileTable(QTableWidget):
    path_columns=(0,)
    def startDrag(self,supportedActions):
        from PySide6.QtCore import QMimeData,QUrl
        from PySide6.QtGui import QDrag
        columns=self.path_columns
        if self.currentColumn() in columns:columns=(self.currentColumn(),)
        paths=[]
        for index in self.selectionModel().selectedRows():
            for col in columns:
                item=self.item(index.row(),col)
                if item:
                    path=item.data(Qt.UserRole) or item.text()
                    if Path(str(path)).exists():paths.append(str(path))
        if paths:
            mime=QMimeData();mime.setUrls([QUrl.fromLocalFile(p) for p in dict.fromkeys(paths)]);drag=QDrag(self);drag.setMimeData(mime);drag.exec(Qt.CopyAction)

class FileTree(QTreeWidget):
    def startDrag(self,supportedActions):
        from PySide6.QtCore import QMimeData,QUrl
        from PySide6.QtGui import QDrag
        paths=[str(item.data(0,Qt.UserRole)) for item in self.selectedItems() if item.data(0,Qt.UserRole)]
        if paths:
            mime=QMimeData();mime.setUrls([QUrl.fromLocalFile(p) for p in paths]);drag=QDrag(self);drag.setMimeData(mime);drag.exec(Qt.CopyAction)
