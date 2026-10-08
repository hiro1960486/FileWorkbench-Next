from ...ui.common import FileTable,FileTree,SortableItem,TreeItem
from pathlib import Path
from datetime import datetime
import subprocess,os
from PySide6.QtCore import Qt
from PySide6.QtWidgets import *
from ...ui import ModuleWidget,PathEdit,run_job
from ...services.recycle_bin import WindowsRecycleBin
from ...services.file_operations import unique_destination

class RecycleModule(ModuleWidget):
    module_name='ごみ箱・復元'
    def __init__(self):
        super().__init__();self.backend=WindowsRecycleBin();self.entries=[];self.history_entries=[]
        layout=QVBoxLayout(self);conditions=QHBoxLayout()
        self.search=PathEdit();self.search.path_dropped.connect(lambda p:self.search.setText(Path(p).name if Path(p).is_file() else p));self.search.setPlaceholderText('名前・元の場所を検索（フォルダーのDDも可能）')
        self.drive=QComboBox();self.drive.addItem('全ドライブ');self.start=QLineEdit();self.start.setPlaceholderText('開始 YYYY-MM-DD HH:MM（空欄=全期間）');self.end=QLineEdit();self.end.setPlaceholderText('終了 YYYY-MM-DD HH:MM')
        for widget in (self.search,self.drive,self.start,self.end):conditions.addWidget(widget)
        layout.addLayout(conditions);self.search.textChanged.connect(self.render);self.search.textChanged.connect(self.render_history);self.drive.currentTextChanged.connect(self.render);self.start.textChanged.connect(self.render);self.end.textChanged.connect(self.render)
        self.tabs=QTabWidget();self.table=FileTable(0,5);self.table.setHorizontalHeaderLabels(['名前','元の場所','削除日時','元フォルダーの状態','種類'])
        self.history_table=FileTable(0,5);self.history_table.setHorizontalHeaderLabels(['元の場所','処理／状態','退避日時','復元先','退避データ'])
        for table in (self.table,self.history_table):
            table.setSelectionMode(QAbstractItemView.ExtendedSelection);table.setSelectionBehavior(QAbstractItemView.SelectRows);table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive);table.horizontalHeader().setStretchLastSection(False)
            table.viewport().setAcceptDrops(True);table.viewport().installEventFilter(self)
            table.setContextMenuPolicy(Qt.CustomContextMenu);table.customContextMenuRequested.connect(lambda pos,t=table:self.menu(t,pos))
        self.tabs.addTab(self.table,'Windowsごみ箱');self.tabs.addTab(self.history_table,'退避履歴から復元');layout.addWidget(self.tabs,1);layout.addWidget(self.status)
        destination=QHBoxLayout();self.output=PathEdit(True);self.output.setPlaceholderText('空欄なら元の場所。任意の復元先をDDできます');pick=QPushButton('復元先を選択');pick.clicked.connect(self.pick_output)
        self.collision=QComboBox();self.collision.addItems(['別名で保存','スキップ']);destination.addWidget(QLabel('復元先'));destination.addWidget(self.output,1);destination.addWidget(pick);destination.addWidget(QLabel('同名時'));destination.addWidget(self.collision);layout.addLayout(destination)
        bottom=QHBoxLayout();refresh=QPushButton('検索・一覧更新');refresh.clicked.connect(self.refresh);clear_filters=QPushButton('検索条件をクリア');clear_filters.clicked.connect(self.clear_filters);restore=QPushButton('復元先を確認して復元');restore.clicked.connect(self.restore_selected)
        open_bin=QPushButton('Windowsごみ箱を開く');open_bin.clicked.connect(self.open_bin)
        self.selected_count=QLabel('選択: 0件');self.table.itemSelectionChanged.connect(self.update_selection_count);self.history_table.itemSelectionChanged.connect(self.update_selection_count);self.tabs.currentChanged.connect(self.update_selection_count)
        bottom.addWidget(refresh);bottom.addWidget(clear_filters);bottom.addWidget(open_bin);bottom.addWidget(self.selected_count);bottom.addStretch();bottom.addWidget(restore);layout.addLayout(bottom)
        self.status.setText('Windowsごみ箱と退避履歴は別の入口です。永久削除はここでは行いません。')
    def update_selection_count(self):
        table=self.table if self.tabs.currentIndex()==0 else self.history_table
        self.selected_count.setText(f'選択: {len(table.selectionModel().selectedRows())}件')
    def pick_output(self):
        folder=QFileDialog.getExistingDirectory(self,'復元先')
        if folder:self.output.setText(folder)
    def open_bin(self):
        if os.name=='nt':subprocess.Popen(['explorer.exe','shell:RecycleBinFolder'])
        else:QMessageBox.information(self,'Windows専用','Windows上で利用できます')
    def clear_filters(self):
        self.search.clear();self.drive.setCurrentIndex(0);self.start.clear();self.end.clear()
        self.render();self.render_history()
    def refresh(self):
        self.status.setText('Windowsごみ箱を検索しています…')
        history_error=''
        try:
            self.history_entries=self.service.history();self.render_history()
        except Exception as exc:
            history_error='退避履歴の読込に失敗: '+str(exc)
        try:
            entries=run_job(self,'Windowsごみ箱を検索',lambda cancel:self.backend.list_entries())
            if entries is None:raise RuntimeError('検索結果を受け取れませんでした。もう一度検索してください。')
            self.entries=entries;self.render()
            if history_error:self.status.setText(self.status.text()+'\n'+history_error)
            return True
        except Exception as exc:
            detail='Windowsごみ箱の検索に失敗しました。\n'+str(exc)+'\n退避履歴は別タブから確認できます。'
            self.status.setText(detail)
            QMessageBox.warning(self,'ごみ箱の検索エラー',detail)
            return False
    def render(self):
        text=self.search.text().casefold();drive=self.drive.currentText()
        rows=[]
        for entry in self.entries:
            date=entry.deleted_at.replace(' ','T')
            start=self.start.text().strip().replace(' ','T');end=self.end.text().strip().replace(' ','T')
            if len(end)==10:end+='T23:59:59.999999'
            if text and text not in (entry.name+' '+entry.original_directory).casefold():continue
            if drive!='全ドライブ' and not entry.original_directory.casefold().startswith(drive.casefold()):continue
            if start and date<start:continue
            if end and date>end:continue
            rows.append(entry)
        self.table.setSortingEnabled(False);self.table.setRowCount(len(rows))
        for i,e in enumerate(rows):
            values=[e.name,e.original_directory,e.deleted_at,'存在' if Path(e.original_directory).is_dir() else '存在しない','フォルダー' if e.is_folder else 'ファイル']
            for c,value in enumerate(values):
                item=SortableItem(value);item.setData(Qt.UserRole,e.item_id);item.setToolTip(value);self.table.setItem(i,c,item)
        self.table.setSortingEnabled(True)
        summary=f'ごみ箱: {len(self.entries)}件 / 表示: {len(rows)}件 / 退避履歴: {len(self.history_entries)}件'
        if self.entries and not rows:summary+='\n検索条件に一致しません。「検索条件をクリア」で全件表示できます。'
        elif not self.entries:summary+='\nごみ箱に項目がありません。'
        self.status.setText(summary)
        drives=sorted({Path(e.original_directory).drive for e in self.entries if Path(e.original_directory).drive})
        for value in drives:
            if self.drive.findText(value)<0:self.drive.addItem(value)
    def render_history(self):
        query=self.search.text().casefold();entries=[e for e in self.history_entries if not query or query in (e['source']+' '+e['operation']+' '+e['state']+' '+e.get('restored_to','')).casefold()]
        self.history_table.setSortingEnabled(False);self.history_table.setRowCount(len(entries))
        for i,e in enumerate(entries):
            values=[e['source'],e['operation']+' / '+e['state'],e['created'],e.get('restored_to',''),e['backup']]
            for c,value in enumerate(values):
                item=SortableItem(value);item.setToolTip(value);item.setData(Qt.UserRole,e['id']);self.history_table.setItem(i,c,item)
        self.history_table.setSortingEnabled(True)
    def selected_ids(self,table):return [table.item(i.row(),0).data(Qt.UserRole) for i in table.selectionModel().selectedRows()]
    def restore_selected(self):
        native=self.tabs.currentIndex()==0;table=self.table if native else self.history_table
        ids=self.selected_ids(table)
        if not ids:return QMessageBox.information(self,'復元','対象を選択してください。Ctrlで個別、Shiftで範囲選択できます。')
        destination=self.output.text() or None;collision='skip' if self.collision.currentIndex()==1 else 'rename'
        if destination and not Path(destination).is_dir():return QMessageBox.warning(self,'復元先','存在するフォルダーを指定してください')
        plans=[]
        try:
            for ident in ids:
                if native:
                    e=next(e for e in self.entries if e.item_id==ident);name=e.name;folder=Path(destination or e.original_directory)
                else:
                    e=next(e for e in self.history_entries if e['id']==ident);source=Path(e['source']);name=source.name;folder=Path(destination) if destination else source.parent
                if not folder.is_dir():raise ValueError('元の場所がありません。任意復元先を選択してください: '+str(folder))
                target=folder/name
                plans.append(str(unique_destination(target)) if collision=='rename' else str(target)+'（同名があればスキップ）')
        except Exception as exc:return QMessageBox.warning(self,'復元先',str(exc))
        dialog=QDialog(self);dialog.setWindowTitle('復元先をチェック・確認');layout=QVBoxLayout(dialog)
        label=QLabel('同名ファイルは上書きしません。実際の保存先は処理結果で確認できます。');label.setWordWrap(True);layout.addWidget(label)
        text=QPlainTextEdit('\n'.join(plans));text.setReadOnly(True);layout.addWidget(text)
        buttons=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel);buttons.accepted.connect(dialog.accept);buttons.rejected.connect(dialog.reject);layout.addWidget(buttons);dialog.resize(800,420)
        if dialog.exec()!=QDialog.Accepted:return
        def execute(cancel):
            results=[]
            from ...services.file_operations import OperationResult
            for ident in ids:
                if cancel():break
                try:
                    result=self.backend.restore(ident,destination,collision) if native else self.service.restore_backup(ident,destination,collision)
                    results.append(result)
                except Exception as exc:results.append(OperationResult('restore',ident,status='失敗',error=str(exc)))
            return results
        results=run_job(self,'復元中',execute)
        self.status.setText('\n'.join(f'{r.status}: {r.target}\n{r.error}' for r in results))
        QMessageBox.information(self,'復元結果・実際の保存先',self.status.text() or '処理なし／停止')
        self.history_entries=self.service.history();self.render_history()
        if native:
            successful={r.source for r in results if r.status=='成功'};self.entries=[e for e in self.entries if e.item_id not in successful];self.render()
    def menu(self,table,pos):
        menu=QMenu(self);restore=menu.addAction('選択項目を復元…');select=menu.addAction('すべて選択');clear=menu.addAction('選択を解除');copy=menu.addAction('表示情報をコピー')
        open_location=menu.addAction('復元先／元の場所を開く');chosen=menu.exec(table.viewport().mapToGlobal(pos))
        if chosen==restore:self.tabs.setCurrentIndex(0 if table is self.table else 1);self.restore_selected()
        elif chosen==select:table.selectAll()
        elif chosen==clear:table.clearSelection()
        elif chosen==copy:QApplication.clipboard().setText('\n'.join('\t'.join(table.item(i.row(),c).text() for c in range(table.columnCount())) for i in table.selectionModel().selectedRows()))
        elif chosen==open_location:
            rows=table.selectionModel().selectedRows()
            if rows:
                row=rows[0].row();location=table.item(row,1).text() if table is self.table else table.item(row,3).text() or str(Path(table.item(row,0).text()).parent)
                from ...core.common import open_default
                path=Path(location);open_default(path if path.is_dir() else path.parent)
