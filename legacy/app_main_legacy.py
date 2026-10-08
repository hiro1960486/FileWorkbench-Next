import csv, hashlib, json, os, re, shutil, subprocess, sys, time, tempfile
from pathlib import Path
from tree_export import scan_tree, export_tree
from safety import key, validate_name, unique_planned, no_replace, identity, restore as restore_files, save_history, load_history, write_log
from send2trash import send2trash
try:
 from PySide6.QtPdf import QPdfDocument
 from PySide6.QtPdfWidgets import QPdfView
 PDF_VIEW=True
except ImportError:PDF_VIEW=False

def resource_path(name):
 return Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parent))/name

from datetime import datetime
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, QUrl, QFileInfo, QEvent, QThread, Signal, QTimer, QSize, QSettings
from PySide6.QtGui import QColor, QIcon, QPixmap, QKeySequence, QAction, QImageReader, QShortcut
from PySide6.QtWidgets import *
try:
 from PySide6.QtMultimedia import QMediaPlayer,QAudioOutput
 from PySide6.QtMultimediaWidgets import QVideoWidget
 MEDIA=True
except ImportError: MEDIA=False

APP='FileWorkbench Next'; VERSION='2.7.1 RC'; IMG={'.png','.jpg','.jpeg','.bmp','.gif','.webp','.ico','.tif','.tiff'}; MEDIA_EXT={'.mp3','.wav','.flac','.ogg','.m4a','.mp4','.mkv','.avi','.mov','.wmv','.webm'}
STYLE='''QWidget{font-family:"Segoe UI","Yu Gothic UI";font-size:12px;background:#F4F9FF;color:#17314F}
QMainWindow,QDialog{background:#F4F9FF} QLabel{background:transparent}
#HeaderCard,#ContentCard,#HomeCard{background:#FFFFFF;border:1px solid #D6E7F7;border-radius:16px}
#Side{background:#EAF5FF;border:1px solid #D3E7F7;border-radius:18px}
#BrandTitle{font-size:24px;font-weight:800;color:#152A45}
#BrandSub{font-size:12px;color:#57718F}
#SectionTitle,#HomeTitle{font-size:16px;font-weight:800;color:#172B47;padding:3px}
#StepButton{font-size:12px;font-weight:700;border-radius:34px;min-width:72px;min-height:66px;padding:4px 9px;background:#FFFFFF;border:2px solid #D7E8F7;color:#294867}
#StepButton:hover{background:#EEF7FF;border-color:#7AB5EE}
#StepButton[selected="true"]{background:#137FEA;color:white;border-color:#137FEA}
#DropZone{background:#F9FCFF;border:2px dashed #83C4FA;border-radius:12px;color:#347CB6;font-size:14px;font-weight:700}
QPushButton{padding:8px 12px;border:1px solid #79B8EF;border-radius:11px;background:#F7FBFF;color:#173554;min-height:22px;font-weight:600}
QPushButton:hover{background:#EAF5FF;border-color:#2E91E9} QPushButton:pressed{background:#D8ECFF}
QPushButton[tone="blue"]{background:#137FEA;border-color:#137FEA;color:#FFFFFF}
QPushButton[tone="mint"]{background:#14B95E;border-color:#14B95E;color:#FFFFFF}
QPushButton[tone="peach"]{background:#FFF1DE;border-color:#F0CB9A;color:#8F5A16}
QPushButton[tone="rose"]{background:#DF3C78;border-color:#DF3C78;color:#FFFFFF}
QPushButton[tone="lilac"]{background:#8A48CB;border-color:#8A48CB;color:#FFFFFF}
QPushButton[selected="true"]{background:#0B80F3;border:1px solid #0B80F3;color:#FFFFFF;font-weight:700}
QPushButton:disabled{background:#EDF2F7;color:#99A7B8;border-color:#DEE6EE}
#NavButton{font-size:13px;text-align:left;padding-left:18px;min-height:42px;border:1.5px solid #3D9AEE;border-radius:11px;background:#F7FBFF;color:#173554}
#NavButton:hover{background:#EAF5FF;border-color:#0B80F3}
#NavButton[selected="true"]{background:#0B80F3;color:#FFFFFF;border-color:#0B80F3}
#PopoutButton{background:#F7FBFF;border:1.5px solid #3D9AEE;border-radius:11px;color:#173554;font-size:20px;font-weight:800;min-width:44px;max-width:44px;min-height:42px;max-height:42px;padding:0}
#PopoutButton:hover{background:#EAF5FF;border-color:#0B80F3;color:#0B5FAA}
#PopoutButton:pressed{background:#D8ECFF}
QTreeWidget,QListWidget,QTableView,QTextEdit,QLineEdit,QComboBox,QSpinBox{background:#FFFFFF;border:1px solid #D2E3F3;border-radius:10px;padding:4px;selection-background-color:#D7EBFF}
QHeaderView::section{background:#EAF4FF;padding:8px;border:0;border-bottom:1px solid #D2E2F1;font-weight:700;color:#294B70}
QTreeWidget::item,QListWidget::item{padding:4px} QTreeWidget::item:selected,QListWidget::item:selected,QTableView::item:selected{background:#CFE8FF;color:#173E69}
QProgressBar{border:1px solid #CEDFF1;border-radius:9px;background:#E9F1FA;text-align:center;min-height:19px} QProgressBar::chunk{background:#55A6F1;border-radius:8px}
QScrollBar:vertical{width:12px;background:#F1F5FB} QScrollBar::handle:vertical{background:#C6D8EC;border-radius:6px;min-height:24px}

#NavButton[navKey="tree"]{background:#EDF6FF;border-color:#78B9F4}
#NavButton[navKey="rename"]{background:#ECFAF2;border-color:#75D0A0}
#NavButton[navKey="preview"]{background:#F6EEFB;border-color:#C49DDB}
#NavButton[navKey="execute"]{background:#FFF4E8;border-color:#F1B46E}
#NavButton[navKey="undo"]{background:#FFF0F5;border-color:#EE9BB9}
#NavButton[navKey="compare"]{background:#ECFAFB;border-color:#74C8D0}
#NavButton[navKey="hash"]{background:#F0F1FC;border-color:#9EA6DE}
#NavButton[selected="true"]{background:#0B80F3;color:#FFFFFF;border-color:#0B80F3}
#FixedActionBar{background:#F3F8FE;border:1px solid #C9DFF3;border-radius:12px}
QToolTip{background:#FFF8E9;color:#465B74;border:1px solid #E7D7B6;padding:5px}'''


def digest(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()

def unique_target(path):
 path=Path(path)
 if not path.exists():return path
 n=1
 while True:
  candidate=path.with_name(f'{path.stem}_{n}{path.suffix}')
  if not candidate.exists():return candidate
  n+=1

class SeekSlider(QSlider):
 """クリック・ドラッグ・キーで任意の位置へ移動するシークバー。"""
 seekRequested=Signal(int)
 def __init__(self):
  super().__init__(Qt.Horizontal);self.setTracking(True)
 def seek_at(self,event):
  option=QStyleOptionSlider();self.initStyleOption(option)
  groove=self.style().subControlRect(QStyle.CC_Slider,option,QStyle.SC_SliderGroove,self)
  handle=self.style().subControlRect(QStyle.CC_Slider,option,QStyle.SC_SliderHandle,self)
  span=max(1,groove.width()-handle.width());position=round(event.position().x()-groove.x()-handle.width()/2)
  value=QStyle.sliderValueFromPosition(self.minimum(),self.maximum(),max(0,min(span,position)),span,option.upsideDown)
  self.setValue(value);self.seekRequested.emit(value)
 def mousePressEvent(self,event):
  if event.button()==Qt.LeftButton and self.isEnabled():self.setSliderDown(True);self.seek_at(event);event.accept();return
  super().mousePressEvent(event)
 def mouseMoveEvent(self,event):
  if self.isSliderDown():self.seek_at(event);event.accept();return
  super().mouseMoveEvent(event)
 def mouseReleaseEvent(self,event):
  if event.button()==Qt.LeftButton and self.isSliderDown():self.seek_at(event);self.setSliderDown(False);event.accept();return
  super().mouseReleaseEvent(event)
 def keyPressEvent(self,event):
  before=self.value();super().keyPressEvent(event)
  if self.value()!=before:self.seekRequested.emit(self.value())

class HashScanWorker(QThread):
 progress=Signal(object)
 result_batch=Signal(object)
 completed=Signal(object)
 failed=Signal(str)
 def __init__(self,files):
  super().__init__();self.files=list(files)
 def cancel(self):self.requestInterruption()
 def run(self):
  started=time.monotonic();records=[];bytes_done=0;total_bytes=0;last=0
  sizes={};batch=[];last_batch=started
  for p in self.files:
   if self.isInterruptionRequested():break
   try:sizes[str(p)]=p.stat().st_size;total_bytes+=sizes[str(p)]
   except OSError:sizes[str(p)]=0
  def report(path,done,force=False):
   nonlocal last
   now=time.monotonic()
   if force or now-last>=0.1:
    last=now;self.progress.emit(dict(done=done,total=len(self.files),path=str(path),bytes=bytes_done,total_bytes=total_bytes,elapsed=now-started))
  try:
   for p in self.files:
    if self.isInterruptionRequested():break
    report(p,len(records),True);record=dict(path=str(p),size='',modified='',sha256='',status='失敗',error='')
    try:
     before=p.stat();record['size']=before.st_size;record['modified']=datetime.fromtimestamp(before.st_mtime).isoformat(timespec='seconds');h=hashlib.sha256()
     with p.open('rb') as f:
      while True:
       if self.isInterruptionRequested():break
       chunk=f.read(1024*1024)
       if not chunk:break
       h.update(chunk);bytes_done+=len(chunk);report(p,len(records))
     if self.isInterruptionRequested():break
     after=p.stat()
     if (before.st_size,before.st_mtime_ns,before.st_ino)!=(after.st_size,after.st_mtime_ns,after.st_ino):raise OSError('読込中にファイルが変更されました')
     record['sha256']=h.hexdigest();record['status']='成功'
    except OSError as exc:record['error']=str(exc)
    records.append(record);batch.append(record);report(p,len(records),True)
    if len(batch)>=100 or time.monotonic()-last_batch>=.15:self.result_batch.emit(list(batch));batch=[];last_batch=time.monotonic()
   for p in self.files[len(records):]:records.append(dict(path=str(p),size=sizes.get(str(p),''),modified='',sha256='',status='未処理',error='キャンセルのため未完了'))
   if batch:self.result_batch.emit(list(batch))
   self.completed.emit(dict(records=records,cancelled=self.isInterruptionRequested(),total=len(self.files),elapsed=time.monotonic()-started))
  except Exception as exc:self.failed.emit(str(exc))

class TaskWorker(QThread):
 completed=Signal(object)
 failed=Signal(str)
 def __init__(self,fn):super().__init__();self.fn=fn
 def run(self):
  try:self.completed.emit(self.fn())
  except Exception as exc:self.failed.emit(str(exc))

class RenameModel(QAbstractTableModel):
 HEAD=['変更前','変更後','状態']; COLORS={'OK':'#15803D','変更なし':'#2563EB','重複':'#DC2626','自動回避':'#7C3AED'}
 def __init__(self):super().__init__();self.rows=[]
 def setRows(self,rows):self.beginResetModel();self.rows=rows;self.endResetModel()
 def rowCount(self,p=QModelIndex()):return 0 if p.isValid() else len(self.rows)
 def columnCount(self,p=QModelIndex()):return 0 if p.isValid() else 3
 def headerData(self,s,o,r=Qt.DisplayRole):return self.HEAD[s] if o==Qt.Horizontal and r==Qt.DisplayRole else None
 def data(self,i,r=Qt.DisplayRole):
  if not i.isValid():return None
  row=self.rows[i.row()];value=[row['old'],row['new'],row['status']][i.column()]
  if r==Qt.DisplayRole:return value
  if r==Qt.ToolTipRole:return value if i.column() in (0,1) else '判定: '+value
  if r==Qt.ForegroundRole:return QColor(self.COLORS.get(row['status'],'#172033'))
  if r==Qt.TextAlignmentRole:return int(Qt.AlignVCenter|(Qt.AlignHCenter if i.column()==2 else Qt.AlignLeft))
  return None

class FileList(QListWidget):
 def __init__(self,owner):
  super().__init__();self.owner=owner;self.setAcceptDrops(True);self.viewport().setAcceptDrops(True);self.setSelectionMode(QAbstractItemView.ExtendedSelection);self.setContextMenuPolicy(Qt.CustomContextMenu);self.customContextMenuRequested.connect(lambda p:owner.file_menu(self,p));self.itemDoubleClicked.connect(lambda i:owner.preview(Path(i.data(Qt.UserRole))) if i.data(Qt.UserRole) else None)

 def dragEnterEvent(self,e):
  if e.mimeData().hasUrls():e.acceptProposedAction()
  else:e.ignore()
 def dragMoveEvent(self,e):e.acceptProposedAction()
 def dropEvent(self,e):
  paths=[Path(u.toLocalFile()) for u in e.mimeData().urls() if u.isLocalFile()]
  if not paths:e.ignore();return
  self.owner.handle_drop(paths,self);e.acceptProposedAction()

class Floating(QWidget):
 def __init__(self,key,title,page,restore):
  super().__init__();self.key=key;self.page=page;self.restore=restore;self.returned=False;self.setWindowTitle(f'{APP} - {title}');self.setStyleSheet(STYLE);self.resize(1050,700);self.setWindowIcon(QIcon(str(resource_path('assets/app.ico'))));lay=QVBoxLayout(self);bar=QHBoxLayout();bar.addWidget(QLabel(f'<b>{title}（切り離し）</b>'));bar.addStretch();back=QPushButton('メインに戻す');back.clicked.connect(self.back);bar.addWidget(back);lay.addLayout(bar);page.setParent(self);page.show();lay.addWidget(page,1)
 def back(self):
  if not self.returned:self.returned=True;self.restore(self.key)
  self.close()
 def closeEvent(self,e):
  if not self.returned:self.returned=True;self.restore(self.key)
  e.accept()

class App(QMainWindow):
 def __init__(self):
  super().__init__();self.setWindowTitle(f'{APP} Ver.{VERSION}');self.resize(1280,780);self.setMinimumSize(820,560);self.setStyleSheet(STYLE);self.setAcceptDrops(True);self.iconp=QFileIconProvider();self.root=None;self.files=[];self.left_root=None;self.right_root=None;self.pages={};self.floaters={};self.preview_path=None;self.preview_files=[];self.preview_index=-1;self.preview_pixmap=None;self.rename_rows=[];self.rename_undo=[];self.compact=False;self.hash_worker=None;self.hash_groups={}
  if MEDIA:self.player=QMediaPlayer();self.audio=QAudioOutput();self.audio.setVolume(.7);self.player.setAudioOutput(self.audio)
  self.task_worker=None;self.task_active=False;self.hash_active=False;self.loading=False;self.closing=False;self.hash_records=[];self.hash_root=None;self.tree_records=[];self.pending_action=None;self.hash_display_active=False;self.hash_render_token=0;self.hash_render_again=False;self.settings=QSettings("hiro1960","FileWorkbenchNext")
  try:self.rename_undo=load_history()
  except Exception as exc:QMessageBox.warning(self,'履歴読込',str(exc))
  self.setWindowIcon(QIcon(str(resource_path('assets/app.ico'))));self.spec_dialog=None;self.nav_buttons={};self.ui();self.style_buttons();self.install_drop_filters();self.fit_path_labels()
 def fit_path_labels(self):
  for label in (self.status,self.hash_current,self.hash_target,self.ptitle,self.left_lab,self.right_lab):label.setMinimumWidth(0);label.setSizePolicy(QSizePolicy.Ignored,QSizePolicy.Preferred);label.setTextFormat(Qt.PlainText)
 def release_preview_for(self,paths):
  if not MEDIA or not self.preview_path:return
  if any(self.preview_path==Path(path) or self.preview_path.is_relative_to(Path(path)) for path in paths):self.player.stop();self.player.setSource(QUrl());self.media_state.setText('ファイル操作のため停止')
 def style_buttons(self):
  # 意味ごとに淡い色を付け、ラベルとアイコンの両方で操作を識別する。
  mapping={'スキャン':('hash','blue'),'実行':('check','mint'),'▶ 再生':('play','mint'),'⏸ 一時停止':('pause','peach'),'⏹ 停止':('stop','rose'),'キャンセル':('stop','rose'),'クリア':('clear','peach'),'CSV出力':('save','mint'),'出力':('save','mint'),'保存先':('folder','blue'),'対象を選択':('folder','blue'),'再スキャン':('hash','blue'),'Undo':('undo','lilac'),'仕様書':('book','lilac'),'フォルダー':('folder','blue'),'ファイル':('file','blue'),'プレビュー':('preview','blue'),'編集':('rename','peach'),'比較':('compare','blue'),'⧉':('pop','lilac'),'☰':('menu','blue'),'消音':('volume','lilac')}
  for button in self.findChildren(QPushButton):
   if button.text() in mapping:
    icon,tone=mapping[button.text()];button.setIcon(QIcon(str(resource_path('assets/'+icon+'.svg'))));button.setIconSize(QSize(18,18));button.setProperty('tone',tone)
    if button.text() in ('▶ 再生','⏸ 一時停止','⏹ 停止'):button.setText(button.text()[2:])
    elif button.text() in ('⧉','☰'):button.setText('');button.setFixedWidth(36)
  self.show_page('tree')
 def open_specification(self):
  path=resource_path('FileWorkbench_Next_Specification_Ver2.7.0_Final.pdf')
  if not path.exists():QMessageBox.warning(self,'仕様書','同梱PDFが見つかりません。ZIPをすべて展開してください。');return
  if not PDF_VIEW:self.open_default(path);return
  if self.spec_dialog is not None:self.spec_dialog.show();self.spec_dialog.raise_();return
  dialog=QDialog(self);dialog.setWindowTitle(APP+' 仕様書 Ver.'+VERSION);dialog.setWindowIcon(self.windowIcon());dialog.resize(1000,720);layout=QVBoxLayout(dialog);bar=QHBoxLayout();bar.addWidget(QLabel('仕様書は上下にスクロールして読めます'));bar.addStretch();zoom=QComboBox();zoom.addItems(['幅に合わせる','ページに合わせる','100%','150%']);bar.addWidget(zoom);layout.addLayout(bar)
  document=QPdfDocument(dialog);error=document.load(str(path))
  if error!=QPdfDocument.Error.None_:QMessageBox.warning(self,'仕様書','PDFを読み込めませんでした。');dialog.deleteLater();return
  view=QPdfView(dialog);view.setDocument(document);view.setPageMode(QPdfView.PageMode.MultiPage);view.setZoomMode(QPdfView.ZoomMode.FitToWidth);layout.addWidget(view,1)
  def zoom_changed(text):
   if text=='幅に合わせる':view.setZoomMode(QPdfView.ZoomMode.FitToWidth)
   elif text=='ページに合わせる':view.setZoomMode(QPdfView.ZoomMode.FitInView)
   else:view.setZoomMode(QPdfView.ZoomMode.Custom);view.setZoomFactor(1.5 if text=='150%' else 1.0)
  zoom.currentTextChanged.connect(zoom_changed);self.spec_dialog=dialog;dialog.show()
 def icon(self,p):
  try:return self.iconp.icon(QFileInfo(str(p)))
  except:return QIcon()
 def page(self,title):
  w=QFrame();w.setObjectName('ContentCard');l=QVBoxLayout(w);l.setContentsMargins(14,12,14,14);heading=QLabel(title);heading.setObjectName('SectionTitle');l.addWidget(heading);return w,l
 def ui(self):
  c=QWidget();self.setCentralWidget(c);outer=QVBoxLayout(c);outer.setContentsMargins(8,8,8,8);outer.setSpacing(8)
  header=QFrame();header.setObjectName('HeaderCard');top=QHBoxLayout(header);top.setContentsMargins(12,8,12,8);top.setSpacing(9)
  self.side_toggle=QPushButton('☰');self.side_toggle.clicked.connect(self.toggle_side);top.addWidget(self.side_toggle)
  logo=QLabel();logo.setPixmap(QIcon(str(resource_path('assets/app.svg'))).pixmap(60,60));top.addWidget(logo)
  brand=QVBoxLayout();title=QLabel(APP);title.setObjectName('BrandTitle');subtitle=QLabel('かんたん・安全・まとめてファイル整理');subtitle.setObjectName('BrandSub');brand.addWidget(title);brand.addWidget(subtitle);top.addLayout(brand);top.addSpacing(14)
  self.workflow_buttons={}
  for key,text,icon_name in [('tree','選んで','file'),('rename','設定して','rename'),('preview','プレビュー','preview'),('execute','実行','play'),('undo','元に戻す','undo')]:
   b=QPushButton(text);b.setObjectName('StepButton');b.setIcon(QIcon(str(resource_path('assets/'+icon_name+'_color.svg'))));b.setIconSize(QSize(30,30))
   if key=='execute':b.clicked.connect(lambda:self.show_page('rename'))
   elif key=='undo':b.clicked.connect(self.rename_undo_last)
   else:b.clicked.connect(lambda _,x=key:self.show_page(x))
   self.workflow_buttons[key]=b;top.addWidget(b)
  top.addStretch();catch=QLabel('ファイル整理で、\nもっと快適な毎日を。');catch.setStyleSheet('font-size:14px;color:#315F94;font-weight:600;padding:0 10px');top.addWidget(catch);self.spec_btn=QPushButton('仕様書');self.spec_btn.clicked.connect(self.open_specification);top.addWidget(self.spec_btn);compact=QPushButton('コンパクト');compact.clicked.connect(self.toggle_compact);top.addWidget(compact);outer.addWidget(header)
  body=QHBoxLayout();self.side=QFrame();self.side.setObjectName('Side');self.side.setMinimumWidth(285);self.side.setMaximumWidth(310);sl=QVBoxLayout(self.side);self.stack=QStackedWidget();self.stack.setAcceptDrops(True)
  defs=[('tree','対象ファイル',self.tree_page()),('rename','リネーム設定',self.rename_page()),('preview','プレビュー',self.preview_page()),('compare','左右比較',self.compare_page()),('hash','HASH・重複',self.hash_page())]
  for k,t,p in defs:
   self.pages[k]=p;row=QHBoxLayout();row.setContentsMargins(4,2,4,2);row.setSpacing(8)
   b=QPushButton(t);b.setObjectName('NavButton');b.setProperty('navKey',k);self.nav_buttons[k]=b
   icon_name={'tree':'folder','rename':'rename','preview':'preview','compare':'compare','hash':'hash'}.get(k,k);b.setIcon(QIcon(str(resource_path('assets/'+icon_name+'_color.svg'))));b.setIconSize(QSize(24,24));b.clicked.connect(lambda _,x=k:self.show_page(x))
   pop=QPushButton('↗');pop.setObjectName('PopoutButton');pop.setToolTip('別ウィンドウで開く');pop.clicked.connect(lambda _,x=k,y=t:self.popout(x,y))
   row.addWidget(b,1);row.addWidget(pop,0);sl.addLayout(row);self.stack.addWidget(p)
  for k,t,icon_name,action in [('execute','実行・出力','play',lambda:self.show_page('rename')),('undo','Undo','undo',self.rename_undo_last)]:
   row=QHBoxLayout();row.setContentsMargins(4,2,4,2);row.setSpacing(8);b=QPushButton(t);b.setObjectName('NavButton');b.setProperty('navKey',k);b.setIcon(QIcon(str(resource_path('assets/'+icon_name+'_color.svg'))));b.setIconSize(QSize(24,24));b.clicked.connect(action);self.nav_buttons[k]=b;pop=QPushButton('↗');pop.setObjectName('PopoutButton');pop.setToolTip('関連画面を開く');pop.clicked.connect(action);row.addWidget(b,1);row.addWidget(pop,0);sl.insertLayout(3 if k=='execute' else 4,row)
  sl.addStretch();body.addWidget(self.side);body.addWidget(self.stack,1);outer.addLayout(body,1)
  bar=QHBoxLayout();choose=QPushButton('フォルダー');choose.clicked.connect(self.choose_root);file=QPushButton('ファイル');file.clicked.connect(self.choose_file);self.status=QLabel('フォルダー／ファイルをこの窓へドロップできます');bar.addWidget(choose);bar.addWidget(file);bar.addWidget(self.status,1);outer.addLayout(bar)
  self.open_folder_action=QAction('フォルダーを開く',self); self.open_folder_action.setShortcut(QKeySequence('Ctrl+O')); self.open_folder_action.setShortcutContext(Qt.ApplicationShortcut); self.open_folder_action.triggered.connect(self.choose_root); self.addAction(self.open_folder_action)
 def install_drop_filters(self):
  targets=[self]+self.findChildren(QWidget)
  for target in targets:
   if target:
    target.setAcceptDrops(True);target.installEventFilter(self)
 def eventFilter(self,obj,event):
  if hasattr(self,'scroll') and obj is self.scroll.viewport() and event.type()==QEvent.Resize:
   QTimer.singleShot(0,self.update_preview_image);return False
  if event.type() in (QEvent.DragEnter,QEvent.DragMove):
   if event.mimeData().hasUrls() and any(u.isLocalFile() for u in event.mimeData().urls()):event.acceptProposedAction();return True
  if event.type()==QEvent.Drop:
   paths=[Path(u.toLocalFile()) for u in event.mimeData().urls() if u.isLocalFile()]
   if paths:self.handle_drop(paths,obj);event.acceptProposedAction();return True
  return super().eventFilter(obj,event)
 def handle_drop(self,paths,widget=None):
  if self.guard():return
  first=paths[0];current=widget;context=None
  while current:
   if current in (self.left,self.left.viewport()):context='left';break
   if current in (self.right,self.right.viewport()):context='right';break
   if current in (self.hash_list,self.hash_list.viewport(),self.pages.get('hash')):context='hash';break
   if current is self.pages.get('tree') or current is self.pages.get('rename'):context='tree';break
   if current is self.pages.get('preview'):context='preview';break
   current=current.parentWidget()
  if context in ('left','right') and first.is_dir():self.set_compare_folder(context,first);return
  if context=='hash' or (context is None and self.stack.currentWidget() is self.pages['hash']):
   if len(paths)==1 and first.is_dir():self.load(first,after='hash')
   else:self.load_hash_sources(paths)
  elif first.is_dir():self.load(first)
  elif first.is_file():self.preview(first)
 def load_hash_sources(self,paths):
  def collect():
   files=[];seen=set()
   for path in paths:
    candidates=[Path(r['path']) for r in scan_tree(path) if r['kind']=='ファイル'] if path.is_dir() else [path]
    for candidate in candidates:
     if candidate.is_file() and key(candidate) not in seen:seen.add(key(candidate));files.append(candidate.absolute())
   return files
  def done(files):
   self.hash_input_files=files;self.pending_action=lambda:self.hash_scan(files=files)
  self.start_task(collect,done)
 def open_default(self,path):
  path=Path(path)
  try:
   if sys.platform.startswith('win'):os.startfile(str(path))
   else:subprocess.Popen(['xdg-open',str(path)])
  except Exception as e:QMessageBox.warning(self,'起動エラー',str(e))
 def open_editor(self,path):
  path=Path(path)
  try:
   if sys.platform.startswith('win'):
    editor=os.environ.get('WINDIR','C:/Windows')+'/System32/notepad.exe'; subprocess.Popen([editor,str(path)])
   else:subprocess.Popen(['xdg-open',str(path)])
  except Exception as e:QMessageBox.warning(self,'編集エラー',str(e))
 def reveal_file(self,path):
  path=Path(path)
  try:
   if sys.platform.startswith('win'):subprocess.Popen(['explorer','/select,',str(path)])
   else:subprocess.Popen(['xdg-open',str(path.parent)])
  except Exception as e:QMessageBox.warning(self,'表示エラー',str(e))
 def toggle_side(self):self.side.setVisible(not self.side.isVisible())
 def toggle_compact(self):self.compact=not self.compact;self.setStyleSheet(STYLE+('QWidget{font-size:10px}QPushButton{padding:3px 6px}' if self.compact else ''))
 def show_page(self,k):
  for key_,button in self.nav_buttons.items():button.setProperty('selected',key_==k);button.style().unpolish(button);button.style().polish(button)
  for key_,button in getattr(self,'workflow_buttons',{}).items():button.setProperty('selected',key_==k);button.style().unpolish(button);button.style().polish(button)
  if k in self.floaters:self.floaters[k].showNormal();self.floaters[k].raise_();return
  self.stack.setCurrentWidget(self.pages[k])
 def popout(self,k,t):
  if k in self.floaters:return self.show_page(k)
  p=self.pages[k];self.stack.removeWidget(p);w=Floating(k,t,p,self.restore);self.floaters[k]=w;w.show()
 def restore(self,k):
  self.floaters.pop(k,None);p=self.pages[k]
  if self.stack.indexOf(p)<0:p.setParent(self.stack);p.show();self.stack.addWidget(p)
  self.show_page(k)
 def tree_page(self):
  w,l=self.page('構成・ツリー');target=QHBoxLayout();self.tree_root_edit=QLineEdit();self.tree_root_edit.setReadOnly(True);self.tree_root_edit.setPlaceholderText('フォルダーを選択するか、ここへドロップ');choose=QPushButton('対象を選択');choose.clicked.connect(self.choose_root);reload=QPushButton('再スキャン');reload.clicked.connect(lambda:self.load(self.root) if self.root else self.choose_root());target.addWidget(self.tree_root_edit,1);target.addWidget(choose);target.addWidget(reload);l.addLayout(target)
  r=QHBoxLayout();exp=QPushButton('全展開');exp.clicked.connect(lambda:self.tree.expandAll());col=QPushButton('全閉じ');col.clicked.connect(lambda:self.tree.collapseAll());self.tree_filter=QLineEdit();self.tree_filter.setPlaceholderText('表示を絞り込み（名前・パス）');self.tree_filter.textChanged.connect(self.filter_tree);self.tree_summary=QLabel('未読込');r.addWidget(exp);r.addWidget(col);r.addWidget(self.tree_filter,1);r.addWidget(self.tree_summary);l.addLayout(r)
  self.tree=QTreeWidget();self.tree.setAcceptDrops(True);self.tree.viewport().setAcceptDrops(True);self.tree.setHeaderLabels(['名前','種類','サイズ','更新日時']);self.tree.header().setSectionResizeMode(0,QHeaderView.Stretch);self.tree.setSelectionMode(QAbstractItemView.ExtendedSelection);self.tree.setContextMenuPolicy(Qt.CustomContextMenu);self.tree.customContextMenuRequested.connect(lambda pos:self.file_menu(self.tree,pos,tree=True));self.tree.itemDoubleClicked.connect(lambda item,_:self.preview(Path(item.data(0,Qt.UserRole))) if item.data(0,Qt.UserRole) and Path(item.data(0,Qt.UserRole)).is_file() else None);l.addWidget(self.tree,1)
  export_row=QHBoxLayout();export_row.addWidget(QLabel('出力形式'));self.tree_format=QComboBox();self.tree_format.addItems(['TXT','CSV','Excel','HTML']);self.tree_format.setCurrentText(self.settings.value('tree_format','HTML'));self.tree_include_files=QCheckBox('ファイルも含む');self.tree_include_files.setChecked(True);self.tree_numbering=QCheckBox('番号を付ける');self.tree_export_btn=QPushButton('出力');self.tree_export_btn.clicked.connect(self.tree_export);export_row.addWidget(self.tree_format);export_row.addWidget(self.tree_include_files);export_row.addWidget(self.tree_numbering);export_row.addStretch();export_row.addWidget(self.tree_export_btn);l.addLayout(export_row)
  destination=QHBoxLayout();destination.addWidget(QLabel('出力先'));self.tree_save_dir=QLineEdit(str(self.settings.value('tree_save_dir','')));self.tree_save_dir.setPlaceholderText('保存するフォルダーを指定');browse=QPushButton('保存先');browse.clicked.connect(self.choose_tree_destination);destination.addWidget(self.tree_save_dir,1);destination.addWidget(browse);destination.addWidget(QLabel('ファイル名'));self.tree_output_name=QLineEdit('directory_structure');self.tree_output_name.setMaximumWidth(220);destination.addWidget(self.tree_output_name);l.addLayout(destination);note=QLabel('出力は読み込み済みの全構成を対象にします。HTMLは折り畳みと元ファイルへのリンクに対応。');l.addWidget(note);return w
 def choose_tree_destination(self):
  folder=QFileDialog.getExistingDirectory(self,'ツリー出力の保存先',self.tree_save_dir.text())
  if folder:self.tree_save_dir.setText(folder);self.settings.setValue('tree_save_dir',folder)
 def filter_tree(self,*_):
  if not hasattr(self,'tree'):return
  text=self.tree_filter.text().strip().casefold();iterator=QTreeWidgetItemIterator(self.tree);items=[]
  while iterator.value():items.append(iterator.value());iterator+=1
  for item in reversed(items):
   match=not text or text in str(item.data(0,Qt.UserRole)).casefold() or any(not item.child(i).isHidden() for i in range(item.childCount()));item.setHidden(not match)
   if text and match and item.childCount():item.setExpanded(True)
 def tree_export(self):
  if self.guard():return
  if not self.tree_records:return QMessageBox.information(self,'ツリー出力','先に対象フォルダーを読み込んでください。')
  if not self.tree_save_dir.text():self.choose_tree_destination()
  directory=Path(self.tree_save_dir.text())
  if not self.tree_save_dir.text():return
  if not directory.is_dir():return QMessageBox.warning(self,'保存先','存在する保存先フォルダーを指定してください。')
  format_name=self.tree_format.currentText();extension={'TXT':'.txt','CSV':'.csv','Excel':'.xlsx','HTML':'.html'}[format_name];name=self.tree_output_name.text().strip()
  try:validate_name(name)
  except ValueError as exc:return QMessageBox.warning(self,'ファイル名',str(exc))
  if not name.lower().endswith(extension):name+=extension
  destination=directory/name
  if destination.exists() and QMessageBox.question(self,'上書き確認',str(destination)+'\nを上書きしますか？')!=QMessageBox.Yes:return
  self.settings.setValue('tree_save_dir',str(directory));self.settings.setValue('tree_format',format_name);snapshot=[dict(r) for r in self.tree_records];root=self.root;include=self.tree_include_files.isChecked();number=self.tree_numbering.isChecked()
  self.start_task(lambda:export_tree(snapshot,root,destination,format_name,include,number),self.tree_export_finished)
 def tree_export_finished(self,path):
  self.status.setText('ツリー出力完了: '+path);QMessageBox.information(self,'出力完了','保存しました:\n'+path)
 def compare_page(self):
  w,l=self.page('左右比較');r=QHBoxLayout();
  for t,fn in [('左選択',lambda:self.choose_compare('left')),('右選択',lambda:self.choose_compare('right')),('比較',self.compare)]:b=QPushButton(t);b.clicked.connect(fn);r.addWidget(b)
  r.addStretch();l.addLayout(r);labs=QHBoxLayout();self.left_lab=QLabel('左: 未選択');self.right_lab=QLabel('右: 未選択');labs.addWidget(self.left_lab);labs.addWidget(self.right_lab);l.addLayout(labs);s=QSplitter();self.left=FileList(self);self.right=FileList(self);s.addWidget(self.left);s.addWidget(self.right);l.addWidget(s);return w
 def rename_page(self):
  w,l=self.page('一括リネーム');s=QSplitter();self.rename_tree=QTreeWidget();self.rename_tree.setHeaderLabel('機能');self.rename_tree.setMaximumWidth(230);groups={'基本変換':[('文字列置換','replace'),('Prefix・Suffix','affix')],'番号・日時':[('連番','sequence'),('日付','date')],'文字変換':[('大小文字','case')],'高度変換':[('正規表現','regex')],'実行管理':[('衝突設定','safety')]}
  for g,items in groups.items():par=QTreeWidgetItem([g]);self.rename_tree.addTopLevelItem(par);[(lambda ch:(ch.setData(0,Qt.UserRole,k),par.addChild(ch)))(QTreeWidgetItem([t])) for t,k in items]
  self.rename_tree.expandAll();self.rename_stack=QStackedWidget();self.rename_pages={};self.rename_widgets={}
  def form(key,fields):
   p=QWidget();f=QFormLayout(p)
   for lab,name,default in fields:e=QLineEdit(default);e.textChanged.connect(lambda _:self.rename_preview());self.rename_widgets[name]=e;f.addRow(lab,e)
   self.rename_pages[key]=p;self.rename_stack.addWidget(p)
  form('replace',[('検索','find',''),('置換（空で削除）','repl','')]);form('affix',[('Prefix','prefix',''),('Suffix','suffix','')]);form('regex',[('正規表現','regex',''),('置換式','regex_repl','')])
  p=QWidget();f=QFormLayout(p);self.seq_start=QSpinBox();self.seq_start.setValue(1);self.seq_digits=QSpinBox();self.seq_digits.setValue(3);self.seq_pattern=QLineEdit('{name}_{num}');f.addRow('開始',self.seq_start);f.addRow('桁数',self.seq_digits);f.addRow('形式',self.seq_pattern);self.rename_pages['sequence']=p;self.rename_stack.addWidget(p)
  p=QWidget();f=QFormLayout(p);self.date_format=QLineEdit('%Y%m%d');self.date_pos=QComboBox();self.date_pos.addItems(['先頭','末尾']);f.addRow('書式',self.date_format);f.addRow('位置',self.date_pos);self.rename_pages['date']=p;self.rename_stack.addWidget(p)
  p=QWidget();f=QFormLayout(p);self.case_mode=QComboBox();self.case_mode.addItems(['小文字','大文字','タイトルケース','拡張子のみ小文字']);f.addRow('変換',self.case_mode);self.rename_pages['case']=p;self.rename_stack.addWidget(p)
  p=QWidget();f=QFormLayout(p);self.collision=QComboBox();self.collision.addItems(['停止','連番で自動回避']);f.addRow('衝突時',self.collision);self.rename_pages['safety']=p;self.rename_stack.addWidget(p)
  self.rename_tree.itemClicked.connect(self.rename_select);s.addWidget(self.rename_tree);s.addWidget(self.rename_stack);pv=QWidget();pl=QVBoxLayout(pv);top=QHBoxLayout();self.rename_count=QLabel('0件');self.rename_limit=QComboBox();self.rename_limit.addItems(['100','500','1000','2000','5000']);self.rename_limit.setCurrentText('1000');self.rename_limit.currentTextChanged.connect(lambda _:self.rename_preview());top.addWidget(self.rename_count);top.addStretch();top.addWidget(QLabel('表示上限'));top.addWidget(self.rename_limit);pl.addLayout(top);self.rename_model=RenameModel();self.rename_table=QTableView();self.rename_table.setModel(self.rename_model);self.rename_table.setWordWrap(False);self.rename_table.setTextElideMode(Qt.ElideMiddle);self.rename_table.setAlternatingRowColors(True);self.rename_table.setSelectionBehavior(QAbstractItemView.SelectRows);self.rename_table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel);header=self.rename_table.horizontalHeader();header.setSectionsMovable(False);header.setStretchLastSection(False);header.setSectionResizeMode(0,QHeaderView.Interactive);header.setSectionResizeMode(1,QHeaderView.Interactive);header.setSectionResizeMode(2,QHeaderView.ResizeToContents);header.resizeSection(0,int(self.settings.value('rename_col_old',420)));header.resizeSection(1,int(self.settings.value('rename_col_new',420)));header.sectionResized.connect(self.rename_column_resized);self.rename_table.doubleClicked.connect(self.rename_detail_dialog);pl.addWidget(self.rename_table);s.addWidget(pv);s.setChildrenCollapsible(False);s.setSizes([210,310,760]);l.addWidget(s,1);action_bar=QFrame();action_bar.setObjectName('FixedActionBar');a=QHBoxLayout(action_bar);a.setContentsMargins(10,8,10,8);self.rename_selected=QCheckBox('ツリーで選択したファイルだけ');self.rename_selected.toggled.connect(lambda _:self.rename_preview());pre=QPushButton('プレビュー更新');pre.clicked.connect(self.rename_preview);dry=QPushButton('ドライラン');dry.clicked.connect(lambda:self.rename_preview(True));undo=QPushButton('Undo');undo.clicked.connect(self.rename_undo_last);run=QPushButton('リネームを実行');run.setProperty('tone','mint');run.setMinimumWidth(170);run.clicked.connect(self.rename_execute);a.addWidget(self.rename_selected);a.addWidget(pre);a.addWidget(dry);a.addStretch();a.addWidget(undo);a.addWidget(run);l.addWidget(action_bar,0);self.rename_tree.setCurrentItem(self.rename_tree.topLevelItem(0).child(0));self.rename_select(self.rename_tree.currentItem());self.tree.itemSelectionChanged.connect(lambda:self.rename_preview());
  for widget in (self.seq_start,self.seq_digits):widget.setRange(0,999999 if widget is self.seq_start else 12);widget.valueChanged.connect(lambda _:self.rename_preview())
  for widget in (self.seq_pattern,self.date_format):widget.textChanged.connect(lambda _:self.rename_preview())
  for widget in (self.date_pos,self.case_mode,self.collision):widget.currentTextChanged.connect(lambda _:self.rename_preview())
  return w
 def hash_page(self):
  w,l=self.page('HASH台帳・重複');r=QHBoxLayout();self.hash_scan_btn=QPushButton('スキャン');self.hash_scan_btn.clicked.connect(self.hash_scan);self.hash_cancel_btn=QPushButton('キャンセル');self.hash_cancel_btn.clicked.connect(self.hash_cancel);self.hash_cancel_btn.setEnabled(False);self.hash_clear_btn=QPushButton('クリア');self.hash_clear_btn.clicked.connect(self.hash_clear);export=QPushButton('CSV出力');export.clicked.connect(self.hash_export);self.hash_export_btn=export;r.addWidget(self.hash_scan_btn);r.addWidget(self.hash_cancel_btn);r.addWidget(self.hash_clear_btn);r.addWidget(export);r.addStretch();l.addLayout(r)
  self.hash_progress=QProgressBar();self.hash_progress.setRange(0,100);self.hash_progress.setValue(0);self.hash_progress.setFormat('%p%');l.addWidget(self.hash_progress)
  info=QHBoxLayout();self.hash_count=QLabel('待機中  0 / 0');self.hash_speed=QLabel('0 MB/s');self.hash_eta=QLabel('残り --:--');info.addWidget(self.hash_count);info.addStretch();info.addWidget(self.hash_speed);info.addWidget(self.hash_eta);l.addLayout(info)
  self.hash_current=QLabel('現在のファイル: なし');self.hash_current.setTextInteractionFlags(Qt.TextSelectableByMouse);l.addWidget(self.hash_current)
  self.hash_mode=QComboBox();self.hash_mode.addItems(['全件台帳','重複のみ','失敗・未処理']);self.hash_mode.currentTextChanged.connect(lambda _:self.render_hash());self.hash_visible_count=QLabel('表示 0件');self.hash_search=QLineEdit();self.hash_search.setPlaceholderText('名前・パス・HASHで絞り込み');self.hash_search.textChanged.connect(lambda _:self.render_hash());filter_row=QHBoxLayout();filter_row.addWidget(self.hash_mode);filter_row.addWidget(self.hash_search,1);filter_row.addWidget(self.hash_visible_count);l.addLayout(filter_row);self.hash_target=QLabel('対象: フォルダーを選択、またはこの画面へドロップ');l.addWidget(self.hash_target);self.hash_list=FileList(self);self.hash_list.setToolTip('フォルダー・ファイルをここへドロップすると自動スキャンし、全件を一覧表示します');l.addWidget(self.hash_list);return w
 def preview_page(self):
  w,l=self.page('プレビュー');r=QHBoxLayout();self.prev_btn=QPushButton('◀ 前へ');self.prev_btn.clicked.connect(lambda:self.preview_step(-1));self.prev_btn.setEnabled(False);self.next_btn=QPushButton('次へ ▶');self.next_btn.clicked.connect(lambda:self.preview_step(1));self.next_btn.setEnabled(False);self.preview_counter=QLabel('0 / 0');self.preview_counter.setAlignment(Qt.AlignCenter);self.ptitle=QLabel('未選択');edit=QPushButton('編集');self.edit_btn=edit;edit.setEnabled(False);edit.clicked.connect(self.edit_current);openb=QPushButton('既定アプリ');openb.clicked.connect(lambda:self.open_default(self.preview_path) if self.preview_path else None);r.addWidget(self.prev_btn);r.addWidget(self.preview_counter);r.addWidget(self.next_btn);r.addWidget(self.ptitle,1);r.addWidget(edit);r.addWidget(openb);l.addLayout(r);self.text=QTextEdit();self.text.setReadOnly(True);self.image=QLabel();self.image.setAlignment(Qt.AlignCenter);self.image.setMinimumSize(1,1);self.scroll=QScrollArea();self.scroll.setWidgetResizable(True);self.scroll.setWidget(self.image);self.scroll.viewport().installEventFilter(self);self.scroll.hide();self.video=QVideoWidget() if MEDIA else QLabel('メディア機能なし');self.video.hide()
  for target in (w,self.text,self.image,self.scroll,self.scroll.viewport(),self.video):target.setContextMenuPolicy(Qt.CustomContextMenu);target.customContextMenuRequested.connect(lambda pos,obj=target:self.preview_context_menu(obj,pos))
  shortcut_prev=QShortcut(QKeySequence(Qt.Key_Left),w);shortcut_prev.activated.connect(lambda:self.preview_step(-1));shortcut_next=QShortcut(QKeySequence(Qt.Key_Right),w);shortcut_next.activated.connect(lambda:self.preview_step(1));l.addWidget(self.text);l.addWidget(self.scroll);l.addWidget(self.video)
  self.media_controls=QWidget();controls=QVBoxLayout(self.media_controls);buttons=QHBoxLayout()
  self.play_btn=QPushButton('▶ 再生');self.pause_btn=QPushButton('⏸ 一時停止');self.stop_btn=QPushButton('⏹ 停止');self.media_time=QLabel('00:00 / 00:00');self.media_state=QLabel('未選択')
  for button in (self.play_btn,self.pause_btn,self.stop_btn):buttons.addWidget(button)
  buttons.addWidget(self.media_state);buttons.addStretch();buttons.addWidget(self.media_time);controls.addLayout(buttons)
  self.seek_slider=SeekSlider();self.seek_slider.setToolTip('クリック・ドラッグで任意の位置へ移動。矢印キーで微調整できます。');self.seek_slider.setRange(0,0);self.seek_slider.setEnabled(False);controls.addWidget(self.seek_slider)
  volume_row=QHBoxLayout();self.mute_btn=QPushButton('消音');self.mute_btn.setCheckable(True);self.volume_slider=QSlider(Qt.Horizontal);self.volume_slider.setRange(0,100);self.volume_slider.setValue(70);self.volume_slider.setMaximumWidth(180);self.volume_label=QLabel('70%');volume_row.addWidget(self.mute_btn);volume_row.addWidget(QLabel('音量'));volume_row.addWidget(self.volume_slider);volume_row.addWidget(self.volume_label);volume_row.addStretch();controls.addLayout(volume_row);l.addWidget(self.media_controls);self.media_controls.hide()
  if MEDIA:
   self.play_btn.clicked.connect(self.player.play);self.pause_btn.clicked.connect(self.player.pause);self.stop_btn.clicked.connect(self.media_stop);self.seek_resume=False;self.seek_slider.sliderPressed.connect(self.media_seek_begin);self.seek_slider.seekRequested.connect(self.media_seek);self.seek_slider.sliderReleased.connect(self.media_seek_commit);self.volume_slider.valueChanged.connect(self.media_volume);self.mute_btn.toggled.connect(self.audio.setMuted);self.player.positionChanged.connect(self.media_position);self.player.durationChanged.connect(self.media_duration);self.player.seekableChanged.connect(lambda _:self.media_seek_enabled());self.player.playbackStateChanged.connect(self.media_playback_state);self.player.errorOccurred.connect(lambda *_:self.media_state.setText('再生エラー: '+self.player.errorString()));self.player.mediaStatusChanged.connect(self.media_status)
  return w
 def media_time_text(self,milliseconds):
  seconds=max(0,int(milliseconds)//1000);hours,seconds=divmod(seconds,3600);minutes,seconds=divmod(seconds,60)
  return f'{hours:02d}:{minutes:02d}:{seconds:02d}' if hours else f'{minutes:02d}:{seconds:02d}'
 def media_position(self,position):
  if self.seek_slider.isSliderDown():return
  if not self.seek_slider.isSliderDown():self.seek_slider.setValue(position)
  self.media_time.setText(self.media_time_text(position)+' / '+self.media_time_text(self.player.duration()))
 def media_seek_begin(self):
  # 動画のデコードに連続シーク要求を送らず、離した時に一度だけ確定する。
  self.seek_resume=self.player.playbackState()==QMediaPlayer.PlayingState
  if self.seek_resume:self.player.pause()
 def media_seek(self,position):
  if self.seek_slider.isSliderDown():
   self.media_time.setText(self.media_time_text(position)+' / '+self.media_time_text(self.player.duration()));return
  self.player.setPosition(position);self.media_position(position)
 def media_seek_commit(self):
  position=self.seek_slider.value();resume=self.seek_resume;self.seek_resume=False
  self.player.setPosition(position);self.media_position(position)
  if resume:self.player.play()
 def media_seek_enabled(self):
  # duration通知後に操作可能にする。ロード途中のseekable=Falseで固定しない。
  self.seek_slider.setEnabled(self.player.duration()>0)

 def media_duration(self,duration):
  self.seek_slider.setRange(0,max(0,duration));self.seek_slider.setSingleStep(1000);self.seek_slider.setPageStep(max(1000,duration//100));self.media_position(self.player.position());self.media_seek_enabled()
 def media_volume(self,value):
  self.audio.setVolume(value/100);self.volume_label.setText(f'{value}%')
 def media_stop(self):
  self.player.stop();self.player.setPosition(0);self.media_position(0)
 def media_playback_state(self,state):
  playing=state==QMediaPlayer.PlayingState;paused=state==QMediaPlayer.PausedState;self.play_btn.setEnabled(not playing);self.pause_btn.setEnabled(playing);self.stop_btn.setEnabled(playing or paused);self.media_state.setText('再生中' if playing else '一時停止' if paused else '停止')
 def media_status(self,status):
  if status==QMediaPlayer.LoadingMedia:self.media_state.setText('読み込み中…')
  elif status==QMediaPlayer.EndOfMedia:self.media_state.setText('再生終了')
  elif status in (QMediaPlayer.LoadedMedia,QMediaPlayer.BufferedMedia):self.media_seek_enabled()

 def choose_root(self):
  f=QFileDialog.getExistingDirectory(self,'フォルダー選択')
  if f:self.load(Path(f))
 def load(self,root,after='tree'):
  if self.guard():return
  root=Path(root).absolute()
  def loaded(records):self.apply_load(root,records,after)
  self.start_task(lambda:scan_tree(root),loaded)
 def apply_load(self,root,records,after='tree'):
  self.loading=True;self.reset_hash();self.root=root;self.hash_input_files=None;self.files=[];self.tree_records=records;self.tree.clear();self.tree_root_edit.setText(str(root));self.hash_target.setText('未スキャン: '+str(root));self.tree_filter.clear();ri=QTreeWidgetItem(self.tree,[root.name or str(root),'フォルダー','','']);ri.setData(0,Qt.UserRole,str(root));ri.setExpanded(True);mapping={'.':ri};items=[r for r in records if r['relative_path']!='.'];offset=0
  def batch():
   nonlocal offset
   try:
    end=min(offset+200,len(items))
    for record in items[offset:end]:
     parent=mapping.get(str(Path(record['relative_path']).parent),ri);item=QTreeWidgetItem(parent,[record['name'],record['kind'],f"{record['size']:,}" if isinstance(record['size'],int) else '',record['modified']]);item.setData(0,Qt.UserRole,record['path']);item.setIcon(0,self.icon(Path(record['path'])));item.setToolTip(0,record['path']+('\n'+record['error'] if record['error'] else ''))
     if record['status']=='失敗':item.setForeground(0,QColor('#DC2626'))
     if record['kind']=='フォルダー':mapping[record['relative_path']]=item
     elif record['kind']=='ファイル':self.files.append(Path(record['path']))
    offset=end;self.status.setText(f'フォルダー表示中 {offset:,}/{len(items):,}')
    if offset<len(items):QTimer.singleShot(0,batch);return
   except Exception as exc:
    self.loading=False;self.pending_action=None;QMessageBox.warning(self,'ツリー表示エラー',str(exc));return
   self.loading=False;failed=sum(r['status']=='失敗' for r in records);folders=sum(r['kind']=='フォルダー' for r in records);self.tree_summary.setText(f'{folders:,}フォルダー / {len(self.files):,}ファイル / 失敗 {failed}');self.status.setText(f'{root}: {len(self.files):,}ファイル');self.rename_preview();self.filter_tree()
   if after=='hash':self.show_page('hash');self.pending_action=lambda:self.hash_scan(files=list(self.files))
   else:self.show_page('tree')
   self.hash_buttons_update();self.drain_pending()
   if self.closing:QTimer.singleShot(0,self.close)
  QTimer.singleShot(0,batch)
 def choose_file(self):
  f,_=QFileDialog.getOpenFileName(self,'ファイル','','すべて (*.*)')
  if f:self.preview(Path(f))
 def choose_compare(self,side):
  f=QFileDialog.getExistingDirectory(self,'比較フォルダー')
  if f:self.set_compare_folder(side,Path(f))
 def set_compare_folder(self,side,root):
  if self.guard():return
  root=Path(root)
  self.start_task(lambda:[p for p in sorted(root.rglob('*')) if p.is_file()],lambda paths:self.apply_compare_folder(side,root,paths))
 def apply_compare_folder(self,side,root,paths):
  root=Path(root)
  if not root.is_dir():return
  widget=self.left if side=='left' else self.right;widget.clear()
  for p in paths:
   if p.is_file():it=QListWidgetItem(self.icon(p),str(p.relative_to(root)));it.setData(Qt.UserRole,str(p));widget.addItem(it)
  if side=='left':self.left_root=root;self.left_lab.setText(f'左: {root}')
  else:self.right_root=root;self.right_lab.setText(f'右: {root}')
  self.status.setText(f'{"左" if side=="left" else "右"}比較フォルダーを読み込みました: {root}')
 def compare(self):
  if self.guard():return
  if not self.left_root or not self.right_root:return QMessageBox.warning(self,'比較','左右を選択してください')
  left,right=self.left_root,self.right_root
  def work():
   lm={p.relative_to(left):p for p in left.rglob('*') if p.is_file()};rm={p.relative_to(right):p for p in right.rglob('*') if p.is_file()};rows=[]
   for rel in sorted(set(lm)|set(rm)):
    a,b=lm.get(rel),rm.get(rel)
    try:status=('サイズ相違' if a.stat().st_size!=b.stat().st_size else '完全一致' if digest(a)==digest(b) else '内容相違') if a and b else '左のみ' if a else '右のみ'
    except OSError as exc:status='読込失敗: '+str(exc)
    rows.append((rel,a,b,status))
   return rows
  self.start_task(work,self.apply_compare)
 def apply_compare(self,rows):
  self.left.clear();self.right.clear();colors={'完全一致':'#15803D','サイズ相違':'#D97706','内容相違':'#DC2626','左のみ':'#2563EB','右のみ':'#7C3AED'}
  for rel,a,b,status in rows:
   for widget,path in ((self.left,a),(self.right,b)):
    it=QListWidgetItem(f'{rel} [{status}]' if path else f'--- [{status}]');it.setForeground(QColor(colors.get(status,'#DC2626')));it.setData(Qt.UserRole,str(path) if path else None);widget.addItem(it)
  self.status.setText(f'比較完了 {len(rows)}件')
 def rename_column_resized(self,index,old_size,new_size):
  if index==0:self.settings.setValue('rename_col_old',new_size)
  elif index==1:self.settings.setValue('rename_col_new',new_size)
 def rename_detail_dialog(self,index):
  if not index.isValid() or index.row()>=len(self.rename_model.rows):return
  row=self.rename_model.rows[index.row()];dialog=QDialog(self);dialog.setWindowTitle('リネーム内容の確認');dialog.setWindowIcon(self.windowIcon());dialog.resize(900,360);layout=QVBoxLayout(dialog)
  info=QLabel('変更前と変更後のフルパスを確認できます。文字列は選択・コピーできます。');layout.addWidget(info)
  form=QFormLayout();old=QLineEdit(row['old']);old.setReadOnly(True);new=QLineEdit(row['new']);new.setReadOnly(True);status=QLineEdit(row['status']);status.setReadOnly(True);form.addRow('変更前',old);form.addRow('変更後',new);form.addRow('状態',status);layout.addLayout(form)
  names=QPlainTextEdit();names.setReadOnly(True);names.setPlainText('変更前:\n'+row['old']+'\n\n変更後:\n'+row['new']);layout.addWidget(names,1)
  buttons=QDialogButtonBox(QDialogButtonBox.Close);buttons.rejected.connect(dialog.reject);layout.addWidget(buttons);dialog.exec()
 def rename_select(self,item,*_):
  k=item.data(0,Qt.UserRole)
  if k in self.rename_pages:self.rename_active=k;self.rename_stack.setCurrentWidget(self.rename_pages[k]);self.rename_preview()
 def renamed(self,p,i):
  stem=p.stem;k=getattr(self,'rename_active','replace')
  if k=='replace' and self.rename_widgets['find'].text():stem=stem.replace(self.rename_widgets['find'].text(),self.rename_widgets['repl'].text())
  elif k=='affix':stem=self.rename_widgets['prefix'].text()+stem+self.rename_widgets['suffix'].text()
  elif k=='sequence':stem=self.seq_pattern.text().replace('{name}',stem).replace('{num}',str(self.seq_start.value()+i).zfill(self.seq_digits.value()))
  elif k=='date':token=datetime.now().strftime(self.date_format.text() or '%Y%m%d');stem=token+'_'+stem if self.date_pos.currentText()=='先頭' else stem+'_'+token
  elif k=='case':stem=stem.lower() if self.case_mode.currentText()=='小文字' else stem.upper() if self.case_mode.currentText()=='大文字' else stem.title() if self.case_mode.currentText()=='タイトルケース' else stem
  elif k=='regex' and self.rename_widgets['regex'].text():stem=re.sub(self.rename_widgets['regex'].text(),self.rename_widgets['regex_repl'].text(),stem)
  suffix=p.suffix.lower() if k=='case' and self.case_mode.currentText()=='拡張子のみ小文字' else p.suffix;return p.with_name(stem+suffix)
 def busy(self):
  return bool(self.loading or self.hash_active or self.task_active or self.hash_display_active)
 def guard(self):
  if self.busy():QMessageBox.information(self,'処理中','処理の完了またはキャンセルを待ってください。');return True
  return False
 def rename_preview(self,dialog=False,*_):
  if not hasattr(self,'collision'):return
  rows=[];reserved={key(p) for p in self.files}
  targets=self.files
  if hasattr(self,'rename_selected') and self.rename_selected.isChecked():
   selected={i.data(0,Qt.UserRole) for i in self.tree.selectedItems() if i.data(0,Qt.UserRole)};targets=[p for p in self.files if str(p) in selected]
  for i,p in enumerate(targets):
   try:
    q=self.renamed(p,i);validate_name(q.name);status='変更なし' if q==p else 'OK'
    if q!=p and key(q)!=key(p) and (key(q) in reserved or q.exists()):
     if self.collision.currentText()=='連番で自動回避':q=unique_planned(q,reserved);status='自動回避'
     else:status='重複'
    reserved.add(key(q))
   except Exception as exc:q=p;status='無効: '+str(exc)
   rows.append(dict(path=p,target=q,old=str(p),new=str(q),status=status))
  self.rename_rows=rows;limit=int(self.rename_limit.currentText());self.rename_model.setRows(rows[:limit]);self.rename_count.setText(f'対象 {len(rows):,} / 表示 {min(len(rows),limit):,}')
  if dialog:QMessageBox.information(self,'ドライラン',f"対象 {len(rows)}件\n変更予定 {sum(r['status'] in ('OK','自動回避') for r in rows)}件\n問題 {sum(r['status']=='重複' or r['status'].startswith('無効') for r in rows)}件")
 def rename_execute(self):
  if self.guard():return
  self.rename_preview()
  if any(r['status']=='重複' or r['status'].startswith('無効') for r in self.rename_rows):return QMessageBox.warning(self,'停止','変更先に重複または無効な名前があります。')
  changes=[r for r in self.rename_rows if r['status'] in ('OK','自動回避')]
  if not changes:return
  if QMessageBox.question(self,'確認',f'{len(changes)}件を変更しますか？')!=QMessageBox.Yes:return
  self.release_preview_for([r['path'] for r in changes]);done=[];self.rename_undo.append(done)
  try:
   save_history(self.rename_undo)
   for r in changes:
    entry=dict(current=str(r['target']),original=str(r['path']),identity=identity(r['path']))
    no_replace(r['path'],r['target']);done.append(entry);save_history(self.rename_undo);write_log('rename',entry['original'],entry['current'],'成功','')
  except Exception as exc:
   remaining,errors=restore_files(done);self.rename_undo[-1]=remaining
   try:write_log('rollback','','','失敗' if errors else '成功','\n'.join(errors))
   except OSError as err:errors.append('ログ保存: '+str(err))
   if not remaining:self.rename_undo.pop()
   try:save_history(self.rename_undo)
   except Exception as err:errors.append('履歴保存: '+str(err))
   QMessageBox.critical(self,'失敗',str(exc)+'\n'+'\n'.join(errors))
  if self.root:self.load(self.root)
 def rename_undo_last(self):
  if self.guard() or not self.rename_undo:return
  self.release_preview_for([entry['current'] for entry in self.rename_undo[-1]])
  remaining,errors=restore_files(self.rename_undo[-1]);self.rename_undo[-1]=remaining
  try:write_log('undo','','','失敗' if errors else '成功','\n'.join(errors))
  except OSError as exc:errors.append('ログ保存: '+str(exc))
  if not remaining:self.rename_undo.pop()
  try:save_history(self.rename_undo)
  except Exception as exc:errors.append(str(exc))
  if errors:QMessageBox.warning(self,'復元できなかった項目','\n'.join(errors))
  if self.root:self.load(self.root)
 def hash_scan(self,checked=False,files=None):
  if self.guard():return
  source=list(files) if files is not None else list(getattr(self,'hash_input_files',None) or self.files)
  if not source:
   if self.root and self.tree_records:self.reset_hash();self.hash_count.setText('完了 対象ファイル 0件');self.hash_list.addItem('このフォルダーにはファイルがありません。');return
   return QMessageBox.warning(self,'スキャン','対象フォルダーを選択、またはフォルダー／ファイルをHASH画面へドロップしてください。')
  self.hash_clear();self.hash_mode.blockSignals(True);self.hash_mode.setCurrentText('全件台帳');self.hash_mode.blockSignals(False);self.hash_root=self.root;self.hash_input_files=source;self.hash_target.setText(f'対象 {len(source):,}ファイル  '+(str(self.root) if self.root and all(p.is_relative_to(self.root) for p in source) else 'ドロップしたファイル／フォルダー'));self.hash_scan_btn.setEnabled(False);self.hash_cancel_btn.setEnabled(True);self.hash_clear_btn.setEnabled(False);self.hash_export_btn.setEnabled(False)
  self.hash_active=True;self.hash_worker=HashScanWorker(source);self.hash_worker.progress.connect(self.hash_progress_update);self.hash_worker.result_batch.connect(self.hash_result_batch);self.hash_worker.completed.connect(self.hash_finished);self.hash_worker.failed.connect(self.hash_failed);self.hash_worker.finished.connect(self.hash_thread_done);self.hash_worker.start();self.status.setText('HASHスキャンを開始しました')
 def hash_thread_done(self):
  self.hash_active=False;self.hash_buttons_update()
  if self.closing and not self.busy():QTimer.singleShot(0,self.close)
 def hash_buttons_update(self):
  ready=not self.busy();self.hash_scan_btn.setEnabled(ready);self.hash_cancel_btn.setEnabled(self.hash_active);self.hash_clear_btn.setEnabled(ready);self.hash_export_btn.setEnabled(ready and bool(self.hash_records))
 def hash_progress_update(self,data):
  self.hash_progress.setRange(0,1000);fraction=data['bytes']/max(data['total_bytes'],1);self.hash_progress.setValue(min(999,int(fraction*1000)));self.hash_progress.setFormat('%p%');self.hash_count.setText(f"スキャン中 {data['done']:,} / {data['total']:,}");speed=data['bytes']/max(data['elapsed'],.001);self.hash_speed.setText(f'{speed/1024/1024:.1f} MB/s');remaining=max(0,data['total_bytes']-data['bytes'])/max(speed,1);m,sec=divmod(int(remaining),60);self.hash_eta.setText(f'残り 約 {m:02d}:{sec:02d}');self.hash_current.setText('現在のファイル: '+data['path'])
 def hash_result_batch(self,rows):
  self.hash_records.extend(rows)
  if self.hash_display_active:self.hash_render_again=True;return
  if self.hash_mode.currentText()=='全件台帳' and not self.hash_search.text().strip():
   for row in rows:self.append_hash_item(row)
   self.hash_visible_count.setText(f'表示 {len(self.hash_records):,}件')
 def hash_cancel(self):
  if self.hash_worker and self.hash_worker.isRunning():self.hash_worker.cancel();self.hash_cancel_btn.setEnabled(False);self.hash_count.setText('キャンセル要求中…')
 def hash_finished(self,result):
  self.hash_records=result['records'];self.hash_groups={}
  for row in self.hash_records:
   if row['status']=='成功':self.hash_groups.setdefault(row['sha256'],[]).append(Path(row['path']))
  success=sum(r['status']=='成功' for r in self.hash_records);failed=sum(r['status']=='失敗' for r in self.hash_records);pending=sum(r['status']=='未処理' for r in self.hash_records);state='キャンセル済み' if result['cancelled'] else '完了';duplicates=sum(len(paths)>1 for paths in self.hash_groups.values());self.hash_count.setText(f'{state} 成功 {success:,} / 失敗 {failed:,} / 未処理 {pending:,} / 重複 {duplicates:,}組');self.hash_current.setText('現在のファイル: なし');self.hash_eta.setText(f"所要 {result['elapsed']:.1f}秒");self.status.setText(self.hash_count.text());self.render_hash()
  if not result['cancelled']:self.hash_progress.setValue(self.hash_progress.maximum())
 def append_hash_item(self,row):
  group=len(self.hash_groups.get(row['sha256'],[]));duplicate=f' [重複 {group}件]' if group>1 else '';item=QListWidgetItem(f"[{row['status']}]{duplicate} {row['path']} | {row['sha256']} {row['error']}");item.setData(Qt.UserRole,row['path']);item.setForeground(QColor('#DC2626' if row['status']=='失敗' else '#31445F'));self.hash_list.addItem(item)
 def render_hash(self):
  if not hasattr(self,'hash_list'):return
  self.hash_render_token+=1;token=self.hash_render_token;self.hash_list.clear();mode=self.hash_mode.currentText();search=self.hash_search.text().strip().casefold();rows=[]
  for row in self.hash_records:
   if mode=='重複のみ' and (row['status']!='成功' or len(self.hash_groups.get(row['sha256'],[]))<2):continue
   if mode=='失敗・未処理' and row['status']=='成功':continue
   if search and search not in (row['path']+' '+row['sha256']+' '+row['error']).casefold():continue
   rows.append(row)
  self.hash_visible_count.setText(f'表示 {len(rows):,} / 台帳 {len(self.hash_records):,}件');self.hash_display_active=True;self.hash_render_again=False;offset=0
  def batch():
   nonlocal offset
   if token!=self.hash_render_token:return
   end=min(offset+200,len(rows))
   for row in rows[offset:end]:self.append_hash_item(row)
   offset=end
   if offset<len(rows):QTimer.singleShot(0,batch);return
   self.hash_display_active=False
   if not rows:
    message='重複ファイルはありません。「全件台帳」で取得済みファイルを確認できます。' if mode=='重複のみ' else '該当するファイルはありません。' if self.hash_records else 'フォルダー／ファイルをドロップするか、対象を選択してスキャンしてください。'
    item=QListWidgetItem(message);item.setFlags(Qt.NoItemFlags);self.hash_list.addItem(item)
   self.hash_buttons_update()
   if self.hash_render_again:self.render_hash()
   if self.closing and not self.busy():QTimer.singleShot(0,self.close)
  QTimer.singleShot(0,batch)
 def hash_failed(self,message):
  self.hash_count.setText('エラーで停止');QMessageBox.critical(self,'スキャンエラー',message)
 def hash_clear(self):
  if self.guard():return
  self.reset_hash()
 def reset_hash(self):
  self.hash_render_token+=1;self.hash_list.clear();self.hash_records=[];self.hash_groups={};self.hash_visible_count.setText('表示 0件');self.hash_search.blockSignals(True);self.hash_search.clear();self.hash_search.blockSignals(False);self.hash_progress.setRange(0,100);self.hash_progress.setValue(0);self.hash_count.setText('待機中 0 / 0');self.hash_speed.setText('0 MB/s');self.hash_eta.setText('残り --:--');self.hash_current.setText('現在のファイル: なし');self.hash_buttons_update()
 def hash_export(self):
  if self.guard():return
  if not self.hash_records:return QMessageBox.information(self,'CSV','先にスキャンしてください。')
  f,_=QFileDialog.getSaveFileName(self,'HASH出力','hash_ledger.csv','CSV (*.csv)')
  if not f:return
  records=list(self.hash_records)
  def write():
   handle=tempfile.NamedTemporaryFile(prefix='.fwn_csv_',suffix='.tmp',dir=str(Path(f).parent),delete=False);temp=Path(handle.name);handle.close()
   try:
    with temp.open('w',newline='',encoding='utf-8-sig') as out:
     w=csv.DictWriter(out,fieldnames=['path','size','modified','sha256','status','error']);w.writeheader();w.writerows(records)
    os.replace(temp,f)
   finally:temp.unlink(missing_ok=True)
   return 'CSV保存: '+f
  self.start_task(write,lambda result:self.status.setText(result))
 def start_task(self,fn,callback):
  if self.guard():return
  worker=TaskWorker(fn);self.task_callback=callback;self.task_active=True;self.task_worker=worker;worker.completed.connect(self.task_completed);worker.failed.connect(self.task_failed);worker.finished.connect(self.task_done);worker.start();self.hash_buttons_update();self.status.setText('処理中…')
 def task_completed(self,result):
  try:self.task_callback(result)
  except Exception as exc:self.loading=False;self.pending_action=None;self.task_failed(str(exc))
 def task_failed(self,message):
  self.status.setText('処理エラー: '+message);QMessageBox.warning(self,'処理エラー',message)
 def task_done(self):
  self.task_active=False;self.hash_buttons_update();self.drain_pending()
  if self.closing and not self.busy():QTimer.singleShot(0,self.close)
 def drain_pending(self):
  if self.pending_action is None or self.busy() or self.closing:return
  action=self.pending_action;self.pending_action=None;action()
 def preview(self,p,keep_sequence=False):
  if self.guard():return
  p=Path(p)
  if not p.exists() or not p.is_file():return
  if not keep_sequence:
   sequence=[Path(x) for x in self.files if Path(x).is_file()]
   if p not in sequence:
    try:sequence=sorted([x for x in p.parent.iterdir() if x.is_file()],key=lambda x:x.name.casefold())
    except OSError:sequence=[p]
   self.preview_files=sequence or [p]
  try:self.preview_index=self.preview_files.index(p)
  except ValueError:self.preview_files=[p];self.preview_index=0
  self.preview_path=p;self.preview_pixmap=None;self.update_preview_navigation();self.edit_btn.setEnabled(p.suffix.lower() not in MEDIA_EXT);self.edit_btn.setToolTip('動画・音楽はテキスト編集できません' if p.suffix.lower() in MEDIA_EXT else 'テキストエディターで開く');self.show_page('preview');self.ptitle.setText(f'{p.name} ({p.stat().st_size:,} bytes)');self.text.hide();self.scroll.hide();self.video.hide();self.media_controls.hide()
  if MEDIA:self.player.stop();self.player.setSource(QUrl())
  if p.suffix.lower() in IMG:
   self.scroll.show()
   def read_image():
    reader=QImageReader(str(p));size=reader.size()
    if size.isValid():size.scale(1600,1200,Qt.KeepAspectRatio);reader.setScaledSize(size)
    image=reader.read()
    if image.isNull():raise OSError(reader.errorString())
    return image
   self.start_task(read_image,self.set_preview_image)
  elif MEDIA and p.suffix.lower() in MEDIA_EXT:
   self.media_controls.show();self.seek_slider.setRange(0,0);self.seek_slider.setEnabled(False);self.media_time.setText('00:00 / 00:00');self.media_state.setText('読み込み中…');self.play_btn.setEnabled(True);self.pause_btn.setEnabled(False);self.stop_btn.setEnabled(False)
   if p.suffix.lower() in {'.mp3','.wav','.flac','.ogg','.m4a'}:self.player.setVideoOutput(None)
   else:self.video.show();self.player.setVideoOutput(self.video)
   self.player.setSource(QUrl.fromLocalFile(str(p)));self.player.play()
  else:
   self.text.show()
   def read_preview():
    with p.open('rb') as f:chunk=f.read(200000)
    return f'{p.name}\nサイズ: {p.stat().st_size:,}\nバイナリファイル（HASHはスキャンで確認）' if b'\0' in chunk[:2048] else chunk.decode('utf-8',errors='replace')[:50000]
   self.start_task(read_preview,self.text.setPlainText)
 def set_preview_image(self,image):
  self.preview_pixmap=QPixmap.fromImage(image);self.update_preview_image()
 def update_preview_image(self):
  if not getattr(self,'preview_pixmap',None) or self.preview_pixmap.isNull() or not hasattr(self,'scroll'):return
  size=self.scroll.viewport().size();self.image.setPixmap(self.preview_pixmap.scaled(max(1,size.width()-12),max(1,size.height()-12),Qt.KeepAspectRatio,Qt.SmoothTransformation))
 def update_preview_navigation(self):
  count=len(getattr(self,'preview_files',[]));index=getattr(self,'preview_index',-1);self.preview_counter.setText(f'{index+1 if index>=0 else 0} / {count}');self.prev_btn.setEnabled(index>0);self.next_btn.setEnabled(0<=index<count-1)
 def preview_step(self,delta):
  index=self.preview_index+delta
  if 0<=index<len(self.preview_files):self.preview(self.preview_files[index],True)
 def remove_previewed_path(self,path):
  path=Path(path);old=self.preview_index;self.preview_files=[p for p in self.preview_files if Path(p)!=path]
  if not self.preview_files:self.preview_path=None;self.preview_index=-1;self.preview_counter.setText('0 / 0');self.ptitle.setText('未選択');self.image.clear();self.text.clear();self.scroll.hide();self.text.show();self.update_preview_navigation();return
  self.preview_index=min(old,len(self.preview_files)-1);self.preview(self.preview_files[self.preview_index],True)
 def preview_context_menu(self,widget,pos):
  if not self.preview_path or not Path(self.preview_path).exists():return
  p=Path(self.preview_path);menu=QMenu(self);prev=menu.addAction('前のファイルへ');prev.setEnabled(self.preview_index>0);nxt=menu.addAction('次のファイルへ');nxt.setEnabled(self.preview_index+1<len(self.preview_files));menu.addSeparator();open_action=menu.addAction('既定のアプリで開く');reveal=menu.addAction('エクスプローラーで選択');menu.addSeparator();copy_action=menu.addAction('指定したフォルダーへコピー…');move_action=menu.addAction('指定したフォルダーへ移動…');duplicate=menu.addAction('同じフォルダーに複製');rename=menu.addAction('名前を変更…');menu.addSeparator();copy_path=menu.addAction('フルパスをコピー');copy_hash=menu.addAction('SHA256をコピー');menu.addSeparator();trash=menu.addAction('ごみ箱へ移動…');action=menu.exec(widget.mapToGlobal(pos))
  if action==prev:self.preview_step(-1);return
  if action==nxt:self.preview_step(1);return
  if action==open_action:self.open_default(p);return
  if action==reveal:self.reveal_file(p);return
  if action==copy_path:QApplication.clipboard().setText(str(p));return
  if action==copy_hash:self.start_task(lambda:digest(p),QApplication.clipboard().setText);return
  if action==rename:
   new,ok=QInputDialog.getText(self,'名前を変更','新しいファイル名',text=p.name)
   if ok and new:
    try:validate_name(new);target=p.with_name(new);self.release_preview_for([p]);no_replace(p,target);self.preview_files=[target if Path(x)==p else Path(x) for x in self.preview_files];self.preview(target,True);write_log('rename',str(p),str(target),'成功','')
    except Exception as exc:QMessageBox.warning(self,'名前変更エラー',str(exc))
   return
  if action in (copy_action,move_action):
   destination=QFileDialog.getExistingDirectory(self,'コピー先フォルダー' if action==copy_action else '移動先フォルダー')
   if not destination:return
   target=unique_target(Path(destination)/p.name)
   try:
    if action==copy_action:shutil.copy2(p,target);write_log('copy',str(p),str(target),'成功','')
    else:self.release_preview_for([p]);shutil.move(str(p),str(target));write_log('move',str(p),str(target),'成功','');self.preview_files=[target if Path(x)==p else Path(x) for x in self.preview_files];self.preview(target,True)
    self.status.setText(('コピー' if action==copy_action else '移動')+'完了: '+str(target))
   except Exception as exc:QMessageBox.warning(self,'ファイル操作エラー',str(exc))
   return
  if action==duplicate:
   target=unique_target(p)
   try:shutil.copy2(p,target);self.preview_files.insert(self.preview_index+1,target);self.update_preview_navigation();write_log('duplicate',str(p),str(target),'成功','');self.status.setText('複製完了: '+str(target))
   except Exception as exc:QMessageBox.warning(self,'複製エラー',str(exc))
   return
  if action==trash:
   if QMessageBox.question(self,'ごみ箱へ移動',f'{p.name} をごみ箱へ移動しますか？')!=QMessageBox.Yes:return
   try:self.release_preview_for([p]);send2trash(str(p.absolute()));write_log('trash',str(p),'','成功','');self.remove_previewed_path(p);self.status.setText('ごみ箱へ移動しました: '+str(p))
   except Exception as exc:QMessageBox.warning(self,'削除エラー',str(exc))
 def edit_current(self):
  if self.guard():return
  if self.preview_path and self.preview_path.suffix.lower() not in MEDIA_EXT:self.open_editor(self.preview_path)
 def dragEnterEvent(self,e):
  if e.mimeData().hasUrls() and any(u.isLocalFile() for u in e.mimeData().urls()):e.acceptProposedAction()
  else:e.ignore()
 def dragMoveEvent(self,e):e.acceptProposedAction()
 def dropEvent(self,e):
  paths=[Path(u.toLocalFile()) for u in e.mimeData().urls() if u.isLocalFile()]
  if not paths:e.ignore();return
  self.handle_drop(paths,self.childAt(e.position().toPoint()));e.acceptProposedAction()
 def selected_paths(self,widget,pos,tree=False):
  if tree:return [Path(i.data(0,Qt.UserRole)) for i in self.tree.selectedItems() if i.data(0,Qt.UserRole)] or ([Path(self.tree.itemAt(pos).data(0,Qt.UserRole))] if self.tree.itemAt(pos) else [])
  return [Path(i.data(Qt.UserRole)) for i in widget.selectedItems() if i.data(Qt.UserRole)] or ([Path(widget.itemAt(pos).data(Qt.UserRole))] if widget.itemAt(pos) and widget.itemAt(pos).data(Qt.UserRole) else [])
 def file_menu(self,widget,pos,tree=False):
  if self.guard():return
  paths=self.selected_paths(widget,pos,tree)
  if not paths:return
  m=QMenu(self);prev=m.addAction('プレビュー');opena=m.addAction('既定アプリで開く');edit=m.addAction('テキスト編集');edit.setEnabled(paths[0].is_file() and paths[0].suffix.lower() not in MEDIA_EXT);exp=m.addAction('エクスプローラーで選択');m.addSeparator();copy=m.addAction('コピー先を選択');move=m.addAction('移動先を選択');dup=m.addAction('同じ場所に複製');m.addSeparator();name=m.addAction('名前を変更');cpath=m.addAction('フルパスをコピー');chash=m.addAction('SHA256をコピー');delete=m.addAction('ごみ箱へ移す');a=m.exec((widget.viewport() if hasattr(widget,'viewport') else widget).mapToGlobal(pos))
  p=paths[0]
  if a==prev and p.is_file():self.preview(p)
  elif a==opena:self.open_default(p)
  elif a==edit and p.is_file() and p.suffix.lower() not in MEDIA_EXT:self.open_editor(p)
  elif a==exp:self.reveal_file(p)
  elif a in (copy,move,dup,delete):
   operation='copy' if a==copy else 'move' if a==move else 'duplicate' if a==dup else 'trash'
   dest=None
   if a in (copy,move):
    dest=QFileDialog.getExistingDirectory(self,'保存先')
    if not dest:return
   if a==delete and QMessageBox.question(self,'削除確認',f'{len(paths)}項目をごみ箱へ移しますか？')!=QMessageBox.Yes:return
   # 親子の重複選択は親だけ処理する。
   selected=[src for src in paths if not any(parent!=src and src.is_relative_to(parent) for parent in paths)]
   if operation in ('move','trash'):self.release_preview_for(selected)
   def work():
    reports=[]
    for src in selected:
     target=None;created=False
     try:
      if operation=='trash':send2trash(str(src.absolute()))
      else:
       target=unique_target(src if operation=='duplicate' else Path(dest)/src.name)
       if src.is_dir() and target.resolve().is_relative_to(src.resolve()):raise ValueError('フォルダー自身の配下は保存先にできません')
       if operation=='move':
        if target.exists():raise FileExistsError(str(target))
        shutil.move(str(src),str(target))
       elif src.is_dir():shutil.copytree(src,target)
       else:
        # 排他作成で既存ファイルへの上書きを防止。
        with src.open('rb') as source, target.open('xb') as out:
         created=True;shutil.copyfileobj(source,out,1024*1024)
        shutil.copystat(src,target)
      state='成功';message=''
     except Exception as exc:
      state='失敗';message=str(exc)
      if created and target:
       try:target.unlink()
       except OSError as cleanup:message+=' / 部分コピー削除失敗: '+str(cleanup)
     reports.append(dict(source=str(src),target=str(target or ''),status=state,error=message))
     try:write_log(operation,str(src),str(target or ''),state,message)
     except OSError as exc:reports.append(dict(source='ログ保存',target='',status='失敗',error=str(exc)))
    return reports
   def done(reports):
    failures=[r for r in reports if r['status']=='失敗'];self.status.setText(f"{operation}: 成功 {sum(r['status']=='成功' for r in reports)} / 失敗 {len(failures)}")
    QMessageBox.information(self,'操作結果','\n'.join(f"[{r['status']}] {r['source']} → {r['target']} {r['error']}" for r in reports))
    # 更新はfinished後に行い、処理中ガードとの競合を避ける。
    if self.root:self.pending_action=lambda:self.load(self.root);self.drain_pending()
   self.start_task(work,done)
  elif a==name:
   new,ok=QInputDialog.getText(self,'名前変更','新しい名前',text=p.name)
   if ok and new:
    self.release_preview_for([p])
    try:validate_name(new);no_replace(p,p.with_name(new));self.load(self.root) if self.root else None
    except Exception as e:QMessageBox.warning(self,'名前変更エラー',str(e))
  elif a==cpath:QApplication.clipboard().setText('\n'.join(map(str,paths)))
  elif a==chash and p.is_file():self.start_task(lambda:digest(p),QApplication.clipboard().setText)

 def closeEvent(self,event):
  if self.busy():
   if not self.closing:
    if QMessageBox.question(self,'処理中','処理の停止／完了を待って終了しますか？',QMessageBox.Yes|QMessageBox.No)!=QMessageBox.Yes:event.ignore();return
    self.closing=True
   if self.hash_worker and self.hash_worker.isRunning():self.hash_worker.cancel()
   self.status.setText('停止／完了を待っています…');event.ignore();return
  for floater in list(self.floaters.values()):floater.close()
  if MEDIA:self.player.stop()
  event.accept()

if __name__=='__main__':app=QApplication(sys.argv);app.setStyle('Fusion');w=App();w.show();sys.exit(app.exec())
