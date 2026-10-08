import json,sys
from datetime import datetime
from PySide6.QtCore import Qt
from PySide6.QtWidgets import *
from ..interfaces import EventBus,ModuleBox,ModuleContext,ContextRouter
from ..module_registry import create_ports,create_port
class DeveloperWorkbench(QMainWindow):
    def __init__(self):
        super().__init__();self.setWindowTitle('FileWorkbench Developer Mode - Module I/F Tester');self.resize(1450,900);self.ports=create_ports();self.bus=EventBus();self.windows=[];self.boxes={};self.independent_ports=[];self.events=[]
        root=QWidget();self.setCentralWidget(root);main=QHBoxLayout(root);left=QFrame();left.setMaximumWidth(360);ll=QVBoxLayout(left);ll.addWidget(QLabel('モジュールI/Fテスター'))
        self.list=QListWidget();ll.addWidget(self.list);self.details=QPlainTextEdit();self.details.setReadOnly(True);ll.addWidget(self.details,1);buttons=QHBoxLayout();embed=QPushButton('組み込み試験');stand=QPushButton('単体ウィンドウ');check=QPushButton('契約試験');embed.clicked.connect(self.embed_selected);stand.clicked.connect(self.open_standalone);check.clicked.connect(self.contract_test);buttons.addWidget(embed);buttons.addWidget(stand);buttons.addWidget(check);ll.addLayout(buttons);maintenance=QHBoxLayout();diagnose=QPushButton('保守診断');diagnose.clicked.connect(self.diagnose);save_log=QPushButton('診断・ログ保存');save_log.clicked.connect(self.save_report);maintenance.addWidget(diagnose);maintenance.addWidget(save_log);ll.addLayout(maintenance);ll.addWidget(QLabel('入力コンテキスト JSON'));self.context=QPlainTextEdit('{\n  "selected_paths": [],\n  "working_directory": "",\n  "options": {}\n}');ll.addWidget(self.context);send=QPushButton('I/Fへ送信');send.clicked.connect(self.send_context);ll.addWidget(send);main.addWidget(left)
        right=QSplitter(Qt.Vertical);self.host=QScrollArea();self.host.setWidgetResizable(True);self.host_content=QWidget();self.host_layout=QVBoxLayout(self.host_content);self.host_layout.addStretch();self.host.setWidget(self.host_content);right.addWidget(self.host);self.log=QPlainTextEdit();self.log.setReadOnly(True);right.addWidget(self.log);right.setSizes([650,200]);main.addWidget(right,1)
        for mid,port in self.ports.items():port.subscribe(self.bus.publish);item=QListWidgetItem(f'{port.descriptor.display_name}  [{mid}]');item.setData(Qt.UserRole,mid);self.list.addItem(item)
        self.bus.subscribe_all(self.on_event);self.router=ContextRouter(self.bus,self.ports);self.bus.subscribe('target.mode_changed',self.show_target_mode)
        self.list.currentItemChanged.connect(self.describe);self.list.setCurrentRow(0)
    def show_target_mode(self,event):
        box=self.boxes.get(event.payload.get('module_id'))
        if box:
            box.shared.blockSignals(True);box.shared.setChecked(event.payload['shared']);box.shared.blockSignals(False)
    def selected(self):return self.ports[self.list.currentItem().data(Qt.UserRole)] if self.list.currentItem() else None
    def describe(self):
        p=self.selected()
        if p:self.details.setPlainText(json.dumps(p.descriptor.__dict__,ensure_ascii=False,indent=2,default=list))
    def embed_selected(self):
        p=self.selected()
        if not p:return
        mid=p.descriptor.module_id
        try:
            if mid in self.boxes:box=self.boxes[mid]
            else:
                box=ModuleBox(p);self.boxes[mid]=box;box.shared.setChecked(self.router.policy.is_shared(mid));box.target_mode_changed.connect(self.router.set_shared_mode)
                box.detached.connect(lambda selected_mid:self.open_detached(selected_mid))
                self.host_layout.insertWidget(self.host_layout.count()-1,box)
            box.host_layout.addWidget(p.create_widget(box.host));p.widget.show()
            self.log.appendPlainText(f'[BOX] {mid} を配置')
        except Exception as exc:self.log.appendPlainText(f'[ERROR] {mid}: {exc}')
    def open_detached(self,module_id):
        p=self.ports[module_id]
        try:
            widget=p.create_widget();widget.setParent(None);widget.setWindowTitle(p.descriptor.display_name+' - 切り離し');widget.show()
            if widget not in self.windows:self.windows.append(widget)
        except Exception as exc:self.log.appendPlainText('[ERROR] '+str(exc))
    def open_standalone(self,module_id=None):
        selected=self.ports.get(module_id) if isinstance(module_id,str) else self.selected()
        if not selected:return
        p=create_port(selected.descriptor.module_id)
        try:
            w=p.create_widget();w.setWindowTitle(p.descriptor.display_name+' - 独立単体試験');p.subscribe(self.on_event);w.show()
            self.windows.append(w);self.independent_ports.append(p);self.log.appendPlainText(f'[STANDALONE] {p.descriptor.module_id} / 独立I/F')
        except Exception as exc:p.shutdown();self.log.appendPlainText(f'[ERROR] {p.descriptor.module_id}: {exc}')
    def diagnose(self):
        import importlib.metadata,platform
        dependencies={}
        for name in ('PySide6','Send2Trash','openpyxl','pyinstaller','pywin32'):
            try:dependencies[name]=importlib.metadata.version(name)
            except importlib.metadata.PackageNotFoundError:dependencies[name]='未導入'+('（Windowsのみ）' if name=='pywin32' and sys.platform!='win32' else '')
        data={'time':datetime.now().isoformat(),'python':sys.version,'platform':platform.platform(),'dependencies':dependencies,
              'modules':{mid:{'version':p.descriptor.version,'error':getattr(p,'error',''),'commands':p.descriptor.commands} for mid,p in self.ports.items()}}
        self.log.appendPlainText('[MAINTENANCE]\n'+json.dumps(data,ensure_ascii=False,indent=2));return data
    def save_report(self):
        path,_=QFileDialog.getSaveFileName(self,'保守診断・イベントログを保存','FileWorkbench_Maintenance.json','JSON (*.json)')
        if not path:return
        try:
            from pathlib import Path
            data=self.diagnose();data['events']=self.events;data['log']=self.log.toPlainText()
            with Path(path).open('x',encoding='utf-8') as out:json.dump(data,out,ensure_ascii=False,indent=2)
            self.log.appendPlainText('[SAVED] '+path)
        except Exception as exc:QMessageBox.warning(self,'ログ保存',str(exc))
    def send_context(self):
        p=self.selected()
        try:data=json.loads(self.context.toPlainText());ctx=ModuleContext(**data);p.receive_context(ctx);self.log.appendPlainText('[CONTEXT] 送信成功')
        except Exception as exc:QMessageBox.warning(self,'I/F入力エラー',str(exc))
    def contract_test(self):
        selected=self.selected()
        if not selected:return
        p=create_port(selected.descriptor.module_id);checks=[]
        try:
            for attr in ('descriptor','create_widget','receive_context','current_context','execute','subscribe','shutdown'):
                checks.append((attr,hasattr(p,attr)))
            if hasattr(p,'error'):raise RuntimeError(p.error)
            checks.append(('widget',isinstance(p.create_widget(),QWidget)))
            events=[];p.subscribe(events.append);p.receive_context(ModuleContext())
            checks.append(('context roundtrip',p.current_context().selected_paths==[]))
            checks.append(('context.received',any(e.name=='context.received' for e in events)))
            checks.append(('commands declaration',set(p.commands)==set(p.descriptor.commands)))
            try:p.execute('__unsupported__');checks.append(('unsupported rejected',False))
            except ValueError:checks.append(('unsupported rejected',True))
            p.shutdown();p.shutdown();checks.append(('shutdown',p.widget is None))
            msg='\n'.join(('OK  ' if ok else 'NG  ')+name for name,ok in checks)
        except Exception as exc:msg='NG  '+str(exc)
        finally:p.shutdown()
        self.log.appendPlainText('[CONTRACT TEST - isolated]\n'+msg);QMessageBox.information(self,'契約試験',msg)
    def on_event(self,event):
        self.events.append({'time':datetime.now().isoformat(),'source':event.source,'name':event.name,'payload':event.payload});self.events=self.events[-1000:]
        destination=event.payload.get('destination','preview' if event.name=='selection.changed' and event.source=='tree' else '-')
        self.log.appendPlainText(f'[{datetime.now().isoformat(timespec="milliseconds")}] {event.source} :: {event.name} :: 宛先={destination} :: {event.payload}')
    def closeEvent(self,event):
        if any(p.widget is not None and p.widget.property('operation_busy') for p in [*self.ports.values(),*self.independent_ports]):
            event.ignore();return
        for port in [*self.ports.values(),*self.independent_ports]:port.shutdown()
        super().closeEvent(event)
def main():
    app=QApplication(sys.argv);w=DeveloperWorkbench();w.show();sys.exit(app.exec())
if __name__=='__main__':main()
