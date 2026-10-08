import sys
from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication,QFrame,QHBoxLayout,QLabel,QMainWindow,QPushButton,QStackedWidget,QVBoxLayout,QWidget,QMessageBox,QFileDialog
from . import APP_NAME,VERSION
from .core.common import app_icon,resource_path
from .module_registry import create_ports,UnavailableModule
from .interfaces import EventBus,ContextRouter,ModuleBox
from .ui import PathEdit
from .ui.hosting import ModuleHostController
class App(QMainWindow):
    def __init__(self):
        super().__init__();self.setWindowTitle(f'{APP_NAME} Ver.{VERSION}');self.setWindowIcon(app_icon());self.resize(1450,900)
        root=QWidget();self.setCentralWidget(root);layout=QHBoxLayout(root);side=QFrame();side.setMaximumWidth(240);sl=QVBoxLayout(side);self.stack=QStackedWidget();layout.addWidget(side);right=QWidget();right_layout=QVBoxLayout(right);right_layout.setContentsMargins(0,0,0,0);right_layout.addWidget(self.stack,1);layout.addWidget(right,1)
        self.ports=create_ports();self.bus=EventBus();self.router=ContextRouter(self.bus,self.ports);self.boxes={}
        for port in self.ports.values():port.subscribe(self.bus.publish)
        for mid,port in self.ports.items():
            try:box=ModuleBox(port)
            except Exception as exc:
                port.shutdown();port=UnavailableModule(mid,str(exc));self.ports[mid]=port;box=ModuleBox(port)
            self.boxes[mid]=box;self.stack.addWidget(box)
            button=QPushButton(port.descriptor.display_name);button.setIcon(QIcon(str(resource_path('assets/'+port.descriptor.icon))))
            button.setIconSize(QSize(24,24));button.setMinimumHeight(48);button.clicked.connect(lambda _,module_id=mid:self.show_module(module_id));sl.addWidget(button)
        self.hosting=ModuleHostController(self,self.ports,self.boxes)
        for mid,box in self.boxes.items():
            box.detached.connect(self.hosting.detach);box.shared.setChecked(self.router.policy.is_shared(mid));box.target_mode_changed.connect(self.router.set_shared_mode)
        common=QHBoxLayout();common.addWidget(QLabel('共通対象'));self.common_path=PathEdit();self.common_path.paths_dropped.connect(lambda paths:self.router.update_shared(paths));self.common_path.returnPressed.connect(self.apply_common_text);common.addWidget(self.common_path,1)
        file_button=QPushButton('共通ファイル');file_button.clicked.connect(self.choose_common_files);folder_button=QPushButton('共通フォルダー');folder_button.clicked.connect(self.choose_common_folder);clear=QPushButton('クリア');clear.clicked.connect(lambda:self.router.update_shared([]))
        common.addWidget(file_button);common.addWidget(folder_button);common.addWidget(clear);right_layout.addLayout(common)
        self.bus.subscribe('target.shared_changed',lambda event:self.common_path.setText(' ; '.join(event.payload.get('selected_paths',[]))))
        self.bus.subscribe('target.mode_changed',self.show_target_mode)
        self.bus.subscribe('module.error',lambda event:self.statusBar().showMessage(str(event.payload)))
        sl.addStretch();note=QLabel('Ctrl: 個別選択\nShift: 範囲選択\n各画面へDDできます');note.setWordWrap(True);sl.addWidget(note)
        self.bus.subscribe('preview.requested',lambda event:self.show_module('preview'))
        self.bus.subscribe('rename.requested',lambda event:self.show_module('rename'))
    def apply_common_text(self):
        from pathlib import Path
        text=self.common_path.text().strip()
        paths=[] if not text else [text] if Path(text).exists() else text.split(' ; ')
        if any(not Path(p).exists() for p in paths):
            QMessageBox.warning(self,'共通対象','存在するファイル／フォルダーを指定してください');return
        self.router.update_shared(paths)
    def choose_common_files(self):
        paths,_=QFileDialog.getOpenFileNames(self,'共通ファイル')
        if paths:self.router.update_shared(paths)
    def choose_common_folder(self):
        path=QFileDialog.getExistingDirectory(self,'共通フォルダー')
        if path:self.router.update_shared([path])
    def show_target_mode(self,event):
        box=self.boxes.get(event.payload.get('module_id'))
        if box:
            box.shared.blockSignals(True);box.shared.setChecked(event.payload['shared']);box.shared.blockSignals(False)
    def show_module(self,module_id):
        if module_id in self.hosting.windows:self.hosting.detach(module_id)
        elif module_id in self.boxes:self.stack.setCurrentWidget(self.boxes[module_id])
    def closeEvent(self,event):
        if self.hosting.busy():QMessageBox.information(self,'処理中','処理の完了または停止を待ってから閉じてください');event.ignore();return
        self.hosting.close_all()
        for port in self.ports.values():port.shutdown()
        super().closeEvent(event)
def main():
    app=QApplication(sys.argv);app.setStyle('Fusion');w=App();w.show()
    if '--smoke-test' in sys.argv:
        # Exercise the bundled UI and resource loading, then exit with a checked status.
        from PySide6.QtCore import QTimer
        from pathlib import Path
        import json
        def finish():
            unavailable={mid:str(port.error) for mid,port in w.ports.items() if isinstance(port,UnavailableModule)}
            missing_modules=sorted({'tree','rename','preview','compare','hash','recycle'}-set(w.ports))
            missing=[name for name in ('assets/app.ico','docs/specifications/FileWorkbench_Next_Specification_Ver2.7.0_Final.pdf') if not resource_path(name).is_file()]
            recycle_error=''
            if '--recycle-self-test' in sys.argv:
                try:
                    from tempfile import TemporaryDirectory
                    from uuid import uuid4
                    from send2trash import send2trash
                    from .ui.common import run_job
                    with TemporaryDirectory() as directory:
                        marker='fwn-search-test-'+uuid4().hex
                        sample=Path(directory)/(marker+'.txt');sample.write_text('isolated recycle search test',encoding='utf-8')
                        send2trash(str(sample))
                        backend=w.ports['recycle'].create_widget().backend
                        entries=run_job(w,'ごみ箱検索の自己診断',lambda cancel:backend.list_entries())
                        if not any(e.name.startswith(marker) for e in entries):raise RuntimeError('削除した自己診断ファイルが一覧にありません')
                        widget=w.ports['recycle'].create_widget();widget.entries=entries;widget.search.setText(marker);widget.render()
                        if widget.table.rowCount()!=1:raise RuntimeError('検索結果を画面の一覧に表示できません')
                except Exception as exc:recycle_error=repr(exc)
            drop_error=''
            if '--dd-self-test' in sys.argv:
                try:
                    from tempfile import TemporaryDirectory
                    from PySide6.QtCore import QMimeData,QUrl,QPoint,QPointF,Qt
                    from PySide6.QtGui import QDragEnterEvent,QDragMoveEvent,QDropEvent
                    with TemporaryDirectory() as directory:
                        for mid in ('tree','hash','recycle'):
                            widget=w.ports[mid].create_widget();before=widget.output.text()
                            mime=QMimeData();mime.setUrls([QUrl.fromLocalFile(directory)])
                            enter=QDragEnterEvent(QPoint(8,8),Qt.CopyAction,mime,Qt.LeftButton,Qt.NoModifier)
                            app.sendEvent(widget.output,enter)
                            move=QDragMoveEvent(QPoint(10,8),Qt.CopyAction,mime,Qt.LeftButton,Qt.NoModifier)
                            app.sendEvent(widget.output,move)
                            drop=QDropEvent(QPointF(10,8),Qt.CopyAction,mime,Qt.LeftButton,Qt.NoModifier)
                            app.sendEvent(widget.output,drop)
                            if not all(e.isAccepted() for e in (enter,move,drop)) or widget.output.text()!=directory:
                                raise RuntimeError(mid+'の下部指定欄でD&Dを受け取れません')
                            widget.output.setText(before)
                except Exception as exc:drop_error=repr(exc)
            report={'drop_error':drop_error,'recycle_error':recycle_error,'version':VERSION,'modules':list(w.ports),'unavailable':unavailable,'missing_resources':missing,'missing_modules':missing_modules}
            index=sys.argv.index('--smoke-test')
            if len(sys.argv)>index+1:Path(sys.argv[index+1]).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
            w.close();app.exit(1 if unavailable or missing or missing_modules or recycle_error or drop_error else 0)
        QTimer.singleShot(1500,finish)
    sys.exit(app.exec())
