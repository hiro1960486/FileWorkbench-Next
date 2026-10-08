from PySide6.QtCore import Signal,QObject
from PySide6.QtWidgets import QMainWindow,QWidget,QVBoxLayout,QPushButton,QCheckBox

class FloatingModule(QMainWindow):
    returned=Signal(str)
    def __init__(self,module_id,port,parent=None,shared_box=None):
        super().__init__(parent);self.module_id=module_id;self.port=port
        self.setWindowTitle(port.descriptor.display_name+' — 切り離し');self.resize(1100,760)
        root=QWidget();layout=QVBoxLayout(root);layout.addWidget(port.create_widget(root),1)
        if shared_box is not None:
            self.shared=QCheckBox('共通対象を使う');self.shared.setChecked(shared_box.shared.isChecked());self.shared.toggled.connect(shared_box.shared.setChecked);shared_box.shared.toggled.connect(self.shared.setChecked);layout.addWidget(self.shared)
        button=QPushButton('元の画面へ戻す');button.clicked.connect(self.close);layout.addWidget(button);self.setCentralWidget(root)
    def closeEvent(self,event):
        if self.port.widget and self.port.widget.property('operation_busy'):
            event.ignore();return
        self.returned.emit(self.module_id);super().closeEvent(event)

class ModuleHostController(QObject):
    """Reusable lifetime controller for a single module widget and its host."""
    def __init__(self,parent,ports,boxes):
        super().__init__(parent);self.ports=ports;self.boxes=boxes;self.windows={}
    def detach(self,module_id):
        if module_id in self.windows:
            self.windows[module_id].show();self.windows[module_id].raise_();return
        window=FloatingModule(module_id,self.ports[module_id],self.parent(),self.boxes.get(module_id));self.windows[module_id]=window
        window.returned.connect(self.attach);window.show()
    def attach(self,module_id):
        box=self.boxes.get(module_id)
        if box:
            widget=self.ports[module_id].create_widget();box.host_layout.addWidget(widget);widget.show()
        window=self.windows.pop(module_id,None)
        if window:window.deleteLater()
    def busy(self):return any(port.widget is not None and port.widget.property('operation_busy') for port in self.ports.values())
    def close_all(self):
        for mid in list(self.windows):self.attach(mid)
