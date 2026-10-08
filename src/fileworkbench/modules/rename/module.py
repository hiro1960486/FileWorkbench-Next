from ...ui.common import FileTable,FileTree,SortableItem,TreeItem
from ...ui import ModuleWidget,PathEdit,run_job
from ...services.naming import RenameRules,build_plan
from pathlib import Path
from PySide6.QtCore import Qt,QSettings
from PySide6.QtWidgets import *
from ...core.safety import validate_name,no_replace,unique_planned,key
from ...core.common import choose_folder,app_icon
class RenameModule(ModuleWidget):
    module_name='一括リネーム'
    def __init__(self):
        super().__init__();self.files=[];self.rows=[];self.settings=QSettings('hiro1960','FileWorkbenchRenameModule');self.setWindowTitle(self.module_name);self.setWindowIcon(app_icon());self.resize(1200,720)
        l=QVBoxLayout(self);form=QHBoxLayout();pick=QPushButton('フォルダー');pick.clicked.connect(self.choose);self.find=QLineEdit();self.find.setPlaceholderText('検索');self.repl=QLineEdit();self.repl.setPlaceholderText('置換');self.prefix=QLineEdit();self.prefix.setPlaceholderText('Prefix');self.suffix=QLineEdit();self.suffix.setPlaceholderText('Suffix');self.filter=QLineEdit();self.filter.setPlaceholderText('結果を絞り込み');[form.addWidget(x) for x in (self.find,self.repl,self.prefix,self.suffix,self.filter)];l.addLayout(form)
        for x in (self.find,self.repl,self.prefix,self.suffix,self.filter):x.textChanged.connect(self.preview)
        mode_bar=QHBoxLayout();self.mode=QComboBox();self.mode.addItems(['ライトモード','詳細モード']);mode_bar.addWidget(QLabel('条件設定'));mode_bar.addWidget(self.mode);mode_bar.addWidget(QLabel('詳細条件はライトモードでは適用されません'));mode_bar.addStretch();l.addLayout(mode_bar)
        self.advanced=QGroupBox('詳細条件');grid=QGridLayout(self.advanced)
        self.regex=QCheckBox('正規表現');self.case_sensitive=QCheckBox('大文字・小文字を区別');self.case_sensitive.setChecked(True);self.trim=QCheckBox('前後の空白を除去');self.letter_case=QComboBox();self.letter_case.addItems(['文字種を維持','小文字','大文字','単語先頭大文字'])
        self.extension=QLineEdit();self.extension.setPlaceholderText('拡張子を変更（空欄で維持）');self.extension_filter=QLineEdit();self.extension_filter.setPlaceholderText('対象拡張子例: jpg,png（空欄で全対象）')
        self.numbering=QCheckBox('連番');self.start=QSpinBox();self.start.setRange(0,1000000000);self.start.setValue(1);self.digits=QSpinBox();self.digits.setRange(1,10);self.digits.setValue(3);self.number_position=QComboBox();self.number_position.addItems(['先頭に連番','末尾に連番']);self.delimiter=QLineEdit('_');self.delimiter.setMaximumWidth(80)
        self.date_source=QComboBox();self.date_source.addItems(['日付を付けない','更新日時','作成日時（OS情報）','現在日時']);self.date_format=QComboBox();self.date_format.addItems(['年月日','年-月-日','年月日_時分秒']);self.date_position=QComboBox();self.date_position.addItems(['先頭に日付','末尾に日付'])
        controls=[self.regex,self.case_sensitive,self.trim,self.letter_case,self.extension,self.extension_filter,self.numbering,QLabel('開始番号'),self.start,QLabel('桁数'),self.digits,self.number_position,QLabel('区切り'),self.delimiter,self.date_source,self.date_format,self.date_position]
        for i,control in enumerate(controls):grid.addWidget(control,i//6,i%6)
        l.addWidget(self.advanced);self.advanced.hide();self.mode.currentIndexChanged.connect(self.change_mode)
        for control in controls:
            if isinstance(control,QLineEdit):control.textChanged.connect(self.preview)
            elif isinstance(control,QComboBox):control.currentIndexChanged.connect(self.preview)
            elif isinstance(control,QCheckBox):control.toggled.connect(self.preview)
            elif isinstance(control,QSpinBox):control.valueChanged.connect(self.preview)
        self.table=FileTable(0,3);self.table.setHorizontalHeaderLabels(['変更前','変更後','状態']);h=self.table.horizontalHeader();h.setSectionResizeMode(0,QHeaderView.Interactive);h.setSectionResizeMode(1,QHeaderView.Interactive);h.setSectionResizeMode(2,QHeaderView.ResizeToContents);h.resizeSection(0,int(self.settings.value('old',450)));h.resizeSection(1,int(self.settings.value('new',450)));h.sectionResized.connect(lambda i,o,n:self.settings.setValue('old' if i==0 else 'new',n) if i in (0,1) else None);self.table.setTextElideMode(Qt.ElideMiddle);self.table.doubleClicked.connect(self.detail);l.addWidget(self.table,1)
        self.register_view(self.table,lambda:self.selected_table_paths(self.table),[('変更候補を更新',self.preview)]);l.addWidget(self.status)
        bar=QFrame();a=QHBoxLayout(bar);pre=QPushButton('プレビュー更新');pre.clicked.connect(self.preview);run=QPushButton('リネームを実行');run.clicked.connect(self.execute);a.addWidget(pick);a.addWidget(pre);self.selected_only=QCheckBox('選択行だけ実行');a.addWidget(self.selected_only);a.addStretch();a.addWidget(run);l.addWidget(bar)
    def choose(self):
        p=choose_folder(self)
        if p:self.input_paths([str(p)])
    def change_mode(self):
        self.advanced.setVisible(self.mode.currentIndex()==1);self.preview()
    def configure_rules(self,payload):
        data=dict(payload);mode=data.pop('mode','advanced');rules=RenameRules(**data)
        fields={'find':self.find,'replacement':self.repl,'prefix':self.prefix,'suffix':self.suffix,'extension':self.extension,'extension_filter':self.extension_filter,'delimiter':self.delimiter}
        for key,control in fields.items():control.setText(str(getattr(rules,key)))
        for key,control in {'regex':self.regex,'case_sensitive':self.case_sensitive,'trim':self.trim,'numbering':self.numbering}.items():control.setChecked(bool(getattr(rules,key)))
        self.start.setValue(rules.start);self.digits.setValue(rules.digits)
        self.letter_case.setCurrentIndex(['keep','lower','upper','title'].index(rules.letter_case));self.number_position.setCurrentIndex(0 if rules.number_position=='prefix' else 1)
        self.date_source.setCurrentIndex(['none','modified','created','now'].index(rules.date_source));self.date_format.setCurrentIndex(['%Y%m%d','%Y-%m-%d','%Y%m%d_%H%M%S'].index(rules.date_format));self.date_position.setCurrentIndex(0 if rules.date_position=='prefix' else 1)
        self.mode.setCurrentIndex(0 if mode=='light' else 1);self.preview()
    def rules(self):
        rules=RenameRules(find=self.find.text(),replacement=self.repl.text(),prefix=self.prefix.text(),suffix=self.suffix.text())
        if self.mode.currentIndex()==1:
            rules.regex=self.regex.isChecked();rules.case_sensitive=self.case_sensitive.isChecked();rules.trim=self.trim.isChecked();rules.letter_case=['keep','lower','upper','title'][self.letter_case.currentIndex()]
            rules.extension=self.extension.text();rules.extension_filter=self.extension_filter.text();rules.numbering=self.numbering.isChecked();rules.start=self.start.value();rules.digits=self.digits.value();rules.number_position='prefix' if self.number_position.currentIndex()==0 else 'suffix';rules.delimiter=self.delimiter.text()
            rules.date_source=['none','modified','created','now'][self.date_source.currentIndex()];rules.date_format=['%Y%m%d','%Y-%m-%d','%Y%m%d_%H%M%S'][self.date_format.currentIndex()];rules.date_position='prefix' if self.date_position.currentIndex()==0 else 'suffix'
        return rules
    def preview(self):
        self.rows=build_plan(self.files,self.rules())
        text=self.filter.text().casefold();rows=[r for r in self.rows if not text or text in (str(r[0])+' '+str(r[1])+' '+r[2]).casefold()];self.table.setSortingEnabled(False);self.table.setRowCount(len(rows))
        for i,row in enumerate(rows):
            for c,v in enumerate(map(str,row)):item=SortableItem(v);item.setToolTip(v);self.table.setItem(i,c,item)
        self.table.setSortingEnabled(True)
    def detail(self,index):
        row=index.row();QMessageBox.information(self,'リネーム内容',self.table.item(row,0).text()+'\n\n↓\n\n'+self.table.item(row,1).text())
    def execute(self):
        selected=set(self.selected_table_paths(self.table))
        changes=[row for row in self.rows if row[2] in ('OK','自動回避') and (not self.selected_only.isChecked() or str(row[0]) in selected)]
        if not changes:return QMessageBox.information(self,'リネーム','変更対象がありません。条件と選択状態を確認してください。')
        detail='\n'.join(str(a.name)+' → '+str(b.name) for a,b,_ in changes[:12])
        if QMessageBox.question(self,'変更前の確認',f'{len(changes)}件を変更します。退避してから実行します。\n\n'+detail)!=QMessageBox.Yes:return
        if self.port:self.port.emit('files.will_change',{'selected_paths':[str(row[0]) for row in changes],'operation':'rename'})
        results=run_job(self,'リネーム処理',lambda cancel:self.service.rename_many([(a,b) for a,b,_ in changes],cancel))
        renamed={r.source:Path(r.target) for r in results if r.status=='成功'};self.files=[renamed.get(str(p),p) for p in self.files];self.preview()
        if self.port:self.port.emit('files.changed',{'results':[r.__dict__ for r in results]})
        self.status.setText('\n'.join(f'{r.status}: {r.source} → {r.target} {r.error}' for r in results))
        QMessageBox.information(self,'処理結果',self.status.text() or '処理なし／停止')
def main():
 import sys
 app=QApplication(sys.argv);w=RenameModule();w.show();sys.exit(app.exec())
if __name__=='__main__':main()
