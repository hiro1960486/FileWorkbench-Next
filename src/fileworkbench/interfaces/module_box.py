from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame,QHBoxLayout,QLabel,QPushButton,QVBoxLayout,QWidget,QCheckBox
class ModuleBox(QFrame):
    detached=Signal(str);activated=Signal(str);target_mode_changed=Signal(str,bool)
    def __init__(self,port,parent=None):
        super().__init__(parent);self.port=port;self.setObjectName('ModuleBox');layout=QVBoxLayout(self)
        head=QHBoxLayout();title=QLabel(port.descriptor.display_name);title.setObjectName('ModuleBoxTitle');head.addWidget(title);head.addWidget(QLabel(port.descriptor.version));head.addStretch();layout.addLayout(head)
        self.host=QWidget();self.host_layout=QVBoxLayout(self.host);self.host_layout.setContentsMargins(0,0,0,0);self.host_layout.addWidget(port.create_widget(self.host));layout.addWidget(self.host,1)
        bottom=QHBoxLayout();self.shared=QCheckBox('共通対象を使う');self.shared.toggled.connect(lambda enabled:self.target_mode_changed.emit(port.descriptor.module_id,enabled));bottom.addWidget(self.shared);bottom.addStretch();detach=QPushButton('別窓で開く');detach.clicked.connect(lambda:self.detached.emit(port.descriptor.module_id));bottom.addWidget(detach);layout.addLayout(bottom)
