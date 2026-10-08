from ...ui.common import FileTable,FileTree,SortableItem,TreeItem
from ...ui import ModuleWidget,PathEdit,run_job
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import *
from ...core.common import choose_folder, digest, app_icon
class CompareModule(ModuleWidget):
    module_name='左右比較'
    def __init__(self):
        super().__init__();self.left_root=self.right_root=None;self.setWindowTitle(self.module_name);self.setWindowIcon(app_icon());self.resize(1100,700)
        l=QVBoxLayout(self);bar=QHBoxLayout();a=QPushButton('左を選択');b=QPushButton('右を選択');run=QPushButton('比較');a.clicked.connect(lambda:self.pick('left'));b.clicked.connect(lambda:self.pick('right'));run.clicked.connect(self.compare);self.diff=QCheckBox('差分のみ');self.diff.toggled.connect(self.render);self.search=QLineEdit();self.search.setPlaceholderText('相対パスで絞り込み');self.search.textChanged.connect(self.render);bar.addWidget(self.diff);bar.addWidget(self.search,1);l.addLayout(bar)
        self.table=FileTable(0,3);self.table.setHorizontalHeaderLabels(['相対パス','左','右／判定']);self.table.horizontalHeader().setSectionResizeMode(0,QHeaderView.Stretch);l.addWidget(self.table);self.rows=[]
        self.table.path_columns=(1,2);self.register_view(self.table,lambda:self.selected_table_paths(self.table,(1,2)),[('比較を実行',self.compare)]);l.addWidget(self.status)
        self.left_path=PathEdit();self.right_path=PathEdit();self.left_path.path_dropped.connect(lambda p:self.set_side('left',p));self.right_path.path_dropped.connect(lambda p:self.set_side('right',p));self.left_path.returnPressed.connect(lambda:self.set_side('left',self.left_path.text()));self.right_path.returnPressed.connect(lambda:self.set_side('right',self.right_path.text()))
        bottom=QHBoxLayout();bottom.addWidget(QLabel('左対象'));bottom.addWidget(self.left_path,1);bottom.addWidget(a);bottom.addWidget(QLabel('右対象'));bottom.addWidget(self.right_path,1);bottom.addWidget(b);swap=QPushButton('⇄ 左右を交換');swap.clicked.connect(self.swap_targets);bottom.addWidget(swap);bottom.addWidget(run);l.addLayout(bottom)
    def swap_targets(self):
        left,right=self.left_path.text(),self.right_path.text();self.left_path.setText(right);self.right_path.setText(left);self.set_side('left',right)
    def set_side(self,side,path):
        getattr(self,side+'_path').setText(str(path))
        options={'left_folder':self.left_path.text(),'right_folder':self.right_path.text()}
        if self.port:
            from ...interfaces import ModuleContext
            self.port.emit('target.individual_requested',{})
            self.port.receive_context(ModuleContext(options=options,source_module='drop'))
    def pick(self,side):
        from PySide6.QtGui import QCursor
        menu=QMenu(self);file_action=menu.addAction('ファイルを選択');folder_action=menu.addAction('フォルダーを選択');selected=menu.exec(QCursor.pos())
        path=QFileDialog.getOpenFileName(self,'比較対象ファイル')[0] if selected==file_action else choose_folder(self) if selected==folder_action else None
        if path:self.set_side(side,path)
    def compare(self):
        if not self.left_root or not self.right_root:return QMessageBox.warning(self,'比較','左右を選択してください。')
        def calculate(cancel):
            if self.left_root.is_file() and self.right_root.is_file():
                label=Path(self.left_root.name+' ⇄ '+self.right_root.name);lm={label:self.left_root};rm={label:self.right_root}
            elif self.left_root.is_dir() and self.right_root.is_dir():
                lm={p.relative_to(self.left_root):p for p in self.left_root.rglob('*') if p.is_file()};rm={p.relative_to(self.right_root):p for p in self.right_root.rglob('*') if p.is_file()}
            else:raise ValueError('左右は両方ファイル、または両方フォルダーで指定してください')
            rows=[]
            for rel in sorted(set(lm)|set(rm)):
                if cancel():break
                a,b=lm.get(rel),rm.get(rel)
                try:status='左のみ' if not b else '右のみ' if not a else 'サイズ相違' if a.stat().st_size!=b.stat().st_size else '完全一致' if digest(a)==digest(b) else '内容相違'
                except OSError as exc:status='読込失敗: '+str(exc)
                rows.append((rel,a,b,status))
            return rows
        self.rows=run_job(self,'左右を比較',calculate);self.render();self.status.setText(f'左: {self.left_root} / 右: {self.right_root} / {len(self.rows)}件'+(' / 停止・途中結果' if self.property('last_job_cancelled') else ''))
    def render(self):
        text=self.search.text().casefold();rows=[r for r in self.rows if (not self.diff.isChecked() or r[3]!='完全一致') and (not text or text in str(r[0]).casefold())];self.table.setSortingEnabled(False);self.table.setRowCount(len(rows))
        colors={'完全一致':'#15803D','サイズ相違':'#D97706','内容相違':'#DC2626','左のみ':'#2563EB','右のみ':'#7C3AED'}
        for i,(rel,a,b,status) in enumerate(rows):
            vals=[str(rel),str(a or ''),f'{b or ""} [{status}]']
            for c,v in enumerate(vals):item=SortableItem(v);item.setToolTip(v);item.setData(Qt.UserRole,str(a) if c==1 and a else str(b) if c==2 and b else '');item.setForeground(QColor(colors.get(status,'#31445F')));self.table.setItem(i,c,item)
        self.table.setSortingEnabled(True)
def main():
 import sys
 app=QApplication(sys.argv);w=CompareModule();w.show();sys.exit(app.exec())
if __name__=='__main__':main()
