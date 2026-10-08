from ...ui.common import FileTable,FileTree,SortableItem,TreeItem
from ...ui import ModuleWidget,PathEdit,run_job
from pathlib import Path
from PySide6.QtWidgets import *
from ...core.common import choose_folder,digest,app_icon
class HashModule(ModuleWidget):
    module_name='HASH・重複'
    def __init__(self):
        super().__init__();self.records=[];self.setWindowTitle(self.module_name);self.setWindowIcon(app_icon());self.resize(1050,700)
        l=QVBoxLayout(self);bar=QHBoxLayout();pick=QPushButton('スキャン');pick.clicked.connect(self.scan);self.mode=QComboBox();self.mode.addItems(['全件','重複のみ']);self.mode.currentTextChanged.connect(self.render);self.search=QLineEdit();self.search.setPlaceholderText('パス・HASH検索');self.search.textChanged.connect(self.render);save=QPushButton('CSV出力');save.clicked.connect(self.export);bar.addWidget(self.mode);bar.addWidget(self.search,1);l.addLayout(bar);self.table=FileTable(0,3);self.table.setHorizontalHeaderLabels(['パス','サイズ','SHA256']);self.table.horizontalHeader().setSectionResizeMode(0,QHeaderView.Stretch);l.addWidget(self.table)
        self.register_view(self.table,lambda:self.selected_table_paths(self.table),[('CSV出力…',self.export)]);l.addWidget(self.status)
        self.input_path=PathEdit();self.input_path.path_dropped.connect(lambda p:self.input_paths([p]));self.input_path.returnPressed.connect(lambda:self.input_paths([self.input_path.text()]));select=QPushButton('対象フォルダー');select.clicked.connect(self.choose_input);self.output=PathEdit(True);destination=QPushButton('出力先');destination.clicked.connect(self.choose_output)
        bottom=QHBoxLayout();bottom.addWidget(QLabel('対象'));bottom.addWidget(self.input_path,1);bottom.addWidget(select);bottom.addWidget(pick);bottom.addWidget(QLabel('CSV出力先'));bottom.addWidget(self.output,1);bottom.addWidget(destination);bottom.addWidget(save);l.addLayout(bottom)
    def choose_input(self):
        path=choose_folder(self)
        if path:self.input_paths([str(path)])
    def scan(self,root=None):
        root=root or getattr(self,'input_root',None) or choose_folder(self)
        if not root:return
        self.input_root=Path(root);self.input_path.setText(str(root))
        def calculate(cancel):
            rows=[];errors=[]
            for path in self.input_root.rglob('*'):
                if cancel():break
                if path.is_file():
                    try:rows.append((path,path.stat().st_size,digest(path)))
                    except OSError as exc:errors.append(str(path)+': '+str(exc))
            return rows,errors
        self.records,errors=run_job(self,'HASHを計算',calculate);self.render()
        self.status.setText(f'対象: {root} / 成功 {len(self.records)}件 / 失敗 {len(errors)}件'+(' / 停止・途中結果' if self.property('last_job_cancelled') else '')+('\n'+'\n'.join(errors[:10]) if errors else ''))
    def refresh_records(self):
        self.records=[row for row in self.records if row[0].is_file()];self.render()
    def render(self):
        groups={}
        for r in self.records:groups.setdefault(r[2],[]).append(r)
        text=self.search.text().casefold();rows=[r for r in self.records if (self.mode.currentText()=='全件' or len(groups[r[2]])>1) and (not text or text in (str(r[0])+' '+r[2]).casefold())];self.table.setSortingEnabled(False);self.table.setRowCount(len(rows))
        for i,r in enumerate(rows):
            for c,v in enumerate((str(r[0]),f'{r[1]:,}',r[2])):self.table.setItem(i,c,SortableItem(v))
        self.table.setSortingEnabled(True)
    def choose_output(self):
        folder=QFileDialog.getExistingDirectory(self,'CSV出力先')
        if folder:self.output.setText(folder)
    def export(self):
        import csv
        from ...services.file_operations import unique_destination
        if not self.output.text():self.choose_output()
        if not self.output.text():return
        folder=Path(self.output.text())
        if not folder.is_dir():return QMessageBox.warning(self,'出力先','フォルダーを指定してください')
        target=unique_destination(folder/'hash_ledger.csv')
        with target.open('x',newline='',encoding='utf-8-sig') as out:
            writer=csv.writer(out);writer.writerow(['path','size','sha256']);writer.writerows(self.records)
        self.status.setText('CSV出力完了: '+str(target));QMessageBox.information(self,'出力完了',str(target))
def main():
 import sys
 app=QApplication(sys.argv);w=HashModule();w.show();sys.exit(app.exec())
if __name__=='__main__':main()
