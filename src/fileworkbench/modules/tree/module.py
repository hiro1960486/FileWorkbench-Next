from ...ui.common import FileTable,FileTree,SortableItem,TreeItem
from ...ui import ModuleWidget,PathEdit,run_job
from pathlib import Path
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import *
from ...core.tree_export import scan_tree, export_tree
from ...core.common import choose_folder, app_icon
class TreeModule(ModuleWidget):
    selection_changed = Signal(list)
    module_name='構成ツリー'
    def __init__(self):
        super().__init__();self.root=None;self.records=[];self.setWindowTitle(self.module_name);self.setWindowIcon(app_icon());self.resize(1000,700)
        l=QVBoxLayout(self);bar=QHBoxLayout();self.path=PathEdit(True);self.path.path_dropped.connect(lambda path:self.input_paths([path]));self.path.returnPressed.connect(lambda:self.input_paths([self.path.text()]));pick=QPushButton('対象フォルダー');pick.clicked.connect(self.choose);self.search=QLineEdit();self.search.setPlaceholderText('名前・パスで絞り込み');self.search.textChanged.connect(self.filter);bar.addWidget(self.path,1);bar.addWidget(self.search);l.addLayout(bar)
        self.tree=FileTree();self.tree.setHeaderLabels(['名前','種類','サイズ','更新日時']);self.tree.header().setSectionResizeMode(0,QHeaderView.Stretch);self.tree.setSortingEnabled(True);l.addWidget(self.tree,1);self.tree.itemSelectionChanged.connect(self.notify_selection)
        self.register_view(self.tree,lambda:[item.data(0,Qt.UserRole) for item in self.tree.selectedItems()], [('構成ツリーを出力…',self.export)])
        l.addWidget(self.status)
        destination=QHBoxLayout();self.output=PathEdit(True);self.filename=QLineEdit('directory_structure');dest=QPushButton('出力先');dest.clicked.connect(self.choose_output);destination.addWidget(QLabel('出力先'));destination.addWidget(self.output,1);destination.addWidget(self.filename);destination.addWidget(dest);l.addLayout(destination)
        out=QHBoxLayout();out.addWidget(pick);self.format=QComboBox();self.format.addItems(['TXT','CSV','Excel','HTML']);self.include=QCheckBox('ファイルも含む');self.include.setChecked(True);self.number=QCheckBox('番号を付ける');save=QPushButton('出力');save.clicked.connect(self.export);out.addWidget(QLabel('出力'));out.addWidget(self.format);out.addWidget(self.include);out.addWidget(self.number);out.addStretch();out.addWidget(save);l.addLayout(out)
    def choose(self):
        p=choose_folder(self)
        if p:self.input_paths([str(p)])
    def load(self,root):
        records=run_job(self,'構成を走査',lambda cancel:scan_tree(root,cancel));self.root=Path(root);self.path.setText(str(root));self.records=records;self.tree.clear();mapping={'.':TreeItem(self.tree,[self.root.name,'フォルダー','',''])}
        for r in self.records:
            if r['relative_path']=='.':continue
            parent=mapping.get(str(Path(r['relative_path']).parent),mapping['.']);item=TreeItem(parent,[r['name'],r['kind'],str(r['size']),r['modified']]);item.setToolTip(0,r['path']);item.setData(0,Qt.UserRole,r['path'])
            if r['kind']=='フォルダー':mapping[r['relative_path']]=item
        mapping['.'].setData(0,Qt.UserRole,str(self.root))
        self.tree.expandToDepth(1);self.status.setText(f'対象: {self.root} / {len(self.records)}項目'+(' / 停止・途中結果' if self.property('last_job_cancelled') else ''))
    def notify_selection(self):
        paths=[item.data(0,Qt.UserRole) for item in self.tree.selectedItems()]
        self.selection_changed.emit([p for p in paths if p])

    def filter(self,text):
        iterator=QTreeWidgetItemIterator(self.tree);items=[];text=text.casefold()
        while iterator.value():items.append(iterator.value());iterator+=1
        for item in reversed(items):
            match=not text or text in item.text(0).casefold() or text in str(item.data(0,Qt.UserRole)).casefold()
            descendant=any(not item.child(i).isHidden() for i in range(item.childCount()))
            item.setHidden(not match and not descendant)
            if item.isHidden() and item.isSelected():item.setSelected(False)
    def choose_output(self):
        path=QFileDialog.getExistingDirectory(self,'出力先フォルダー')
        if path:self.output.setText(path)
    def export(self):
        if not self.records:return QMessageBox.information(self,'出力','先に対象を選択してください。')
        from ...services.file_operations import unique_destination
        from ...core.safety import validate_name
        try:
            folder=Path(self.output.text()) if self.output.text() else None
            if folder is None:
                self.choose_output();folder=Path(self.output.text()) if self.output.text() else None
            if folder is None:return
            if not folder.is_dir():raise ValueError('出力先フォルダーが存在しません')
            name=self.filename.text();validate_name(name)
            ext={'TXT':'.txt','CSV':'.csv','Excel':'.xlsx','HTML':'.html'}[self.format.currentText()]
            target=unique_destination(folder/(name+ext))
            export_tree(self.records,self.root,target,self.format.currentText(),self.include.isChecked(),self.number.isChecked())
            self.status.setText('出力完了: '+str(target.absolute()));QMessageBox.information(self,'出力完了',str(target.absolute()))
        except Exception as exc:QMessageBox.warning(self,'出力エラー',str(exc))
def main():
    import sys
    app=QApplication(sys.argv);w=TreeModule();w.show();sys.exit(app.exec())
if __name__=='__main__':main()
