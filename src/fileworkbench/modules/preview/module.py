from pathlib import Path
from PySide6.QtCore import Qt,QUrl,QSize
from PySide6.QtGui import QPixmap,QMovie
from PySide6.QtWidgets import *
from ...ui import ModuleWidget
from ...core.common import app_icon
from .renderers import MEDIA,read_content
from ...services.playback import QtPlaybackService

class SeekSlider(QSlider):
    def mousePressEvent(self,event):
        if event.button()==Qt.LeftButton:
            value=QStyle.sliderValueFromPosition(self.minimum(),self.maximum(),int(event.position().x()),max(1,self.width()))
            self.setValue(value);self.sliderMoved.emit(value);self.sliderReleased.emit();event.accept()
        else:super().mousePressEvent(event)

class PreviewModule(ModuleWidget):
    module_name='プレビュー'
    def __init__(self):
        super().__init__();self.files=[];self.index=-1;self.pdf=None;self.pdf_page=0;self.movie=None;self.player=None;self.playback=None;self.duration=0;self.source_pixmap=None
        self.setWindowTitle(self.module_name);self.setWindowIcon(app_icon());self.resize(1100,760)
        layout=QVBoxLayout(self);self.path=QLabel('ここへファイルをドロップ');self.path.setTextInteractionFlags(Qt.TextSelectableByMouse);layout.addWidget(self.path)
        self.stack=QStackedWidget();self.scroll=QScrollArea();self.scroll.setWidgetResizable(True)
        self.image=QLabel();self.image.setAlignment(Qt.AlignCenter);self.scroll.setWidget(self.image);self.stack.addWidget(self.scroll)
        self.text=QPlainTextEdit();self.text.setReadOnly(True);self.stack.addWidget(self.text)
        try:
            from PySide6.QtMultimediaWidgets import QVideoWidget
            self.video=QVideoWidget();self.stack.addWidget(self.video)
            self.playback=QtPlaybackService(self,self.video);self.player=self.playback.player;self.audio=self.playback.audio
            self.player.durationChanged.connect(self.set_duration);self.player.positionChanged.connect(self.set_position)
            self.player.seekableChanged.connect(lambda value:self.seek.setEnabled(value))
            self.player.errorOccurred.connect(lambda *args:self.status.setText('再生エラー: '+self.player.errorString()))
        except ImportError:self.video=None
        layout.addWidget(self.stack,1);layout.addWidget(self.status)
        media=QHBoxLayout();self.play=QPushButton('▶ 再生');self.pause=QPushButton('一時停止');self.stop=QPushButton('■ 停止')
        self.play.clicked.connect(self.play_media);self.pause.clicked.connect(self.pause_media);self.stop.clicked.connect(self.stop_media)
        self.seek=SeekSlider(Qt.Horizontal);self.seek.setRange(0,10000);self.seek.setEnabled(False)
        self.seek.sliderMoved.connect(self.seek_to);self.time=QLabel('0:00 / 0:00')
        self.volume=QSlider(Qt.Horizontal);self.volume.setRange(0,100);self.volume.setValue(70);self.volume.setMaximumWidth(100)
        self.volume.valueChanged.connect(lambda value:self.audio.setVolume(value/100) if self.player else None)
        if self.player:self.audio.setVolume(.7)
        for widget in (self.play,self.pause,self.stop,self.seek,self.time,QLabel('音量'),self.volume):media.addWidget(widget)
        layout.addLayout(media)
        bottom=QHBoxLayout();pick=QPushButton('ファイルを選択');pick.clicked.connect(self.pick)
        prev=QPushButton('◀ 前のファイル');prev.clicked.connect(lambda:self.step(-1));nxt=QPushButton('次のファイル ▶');nxt.clicked.connect(lambda:self.step(1));self.count=QLabel('0 / 0')
        self.pdf_prev=QPushButton('PDF前ページ');self.pdf_next=QPushButton('PDF次ページ');self.pdf_prev.clicked.connect(lambda:self.step_pdf(-1));self.pdf_next.clicked.connect(lambda:self.step_pdf(1))
        for widget in (pick,prev,self.count,nxt,self.pdf_prev,self.pdf_next):bottom.addWidget(widget)
        bottom.addStretch();layout.addLayout(bottom)
        for view in (self.image,self.text):self.register_view(view,self.current_paths, [('前のファイル',lambda:self.step(-1)),('次のファイル',lambda:self.step(1))])
        self.scroll.viewport().setAcceptDrops(True);self.scroll.viewport().installEventFilter(self)
        if self.video:self.register_view(self.video,self.current_paths)
        self.set_media_enabled(False)
    def current_paths(self):return [self.files[self.index]] if 0<=self.index<len(self.files) else []
    def set_files(self,paths):
        self.release();self.files=[Path(p) for p in paths if Path(p).is_file()];self.index=0 if self.files else -1
        if self.files:self.show_file()
        else:self.image.clear();self.image.setToolTip('');self.text.clear();self.path.setText('ここへファイルをドロップ');self.count.setText('0 / 0');self.stack.setCurrentWidget(self.scroll)
    def pick(self):
        f,_=QFileDialog.getOpenFileName(self,'ファイル')
        if f:
            if self.port:self.port.emit('target.individual_requested',{})
            self.files=sorted(p for p in Path(f).parent.iterdir() if p.is_file());self.index=self.files.index(Path(f));self.show_file()
    def step(self,delta):
        if 0<=self.index+delta<len(self.files):self.index+=delta;self.show_file()
    def set_media_enabled(self,enabled):
        for control in (self.play,self.pause,self.stop,self.volume):control.setEnabled(enabled and self.player is not None)
        self.seek.setEnabled(False)
    def release(self):
        if self.playback:self.playback.close()
        if self.movie:self.movie.stop();self.movie.deleteLater();self.movie=None
        if self.pdf:
            # Detach the Qt owner so dropping the last reference destroys the document
            # immediately and releases its Windows file handle before cleanup/rename.
            pdf,self.pdf=self.pdf,None
            pdf.close();pdf.setParent(None)
            del pdf
        self.duration=0;self.source_pixmap=None
        if hasattr(self,'seek'):self.seek.setValue(0);self.time.setText('0:00 / 0:00');self.set_media_enabled(False)
    def show_file(self):
        self.release()
        if not self.current_paths():return
        p=self.files[self.index];self.path.setText(str(p));self.count.setText(f'{self.index+1} / {len(self.files)}');self.image.clear();self.image.setToolTip(str(p))
        self.pdf_prev.setEnabled(False);self.pdf_next.setEnabled(False)
        try:
            if p.suffix.lower() in MEDIA:
                if not self.player:raise RuntimeError('メディア機能が利用できません。既定アプリで開いてください')
                self.stack.setCurrentWidget(self.video);self.playback.load(p);self.set_media_enabled(True);self.status.setText('再生を押してください。対応形式は搭載コーデックによります');return
            if p.suffix.lower()=='.pdf':
                from PySide6.QtPdf import QPdfDocument
                self.pdf=QPdfDocument(self);error=self.pdf.load(str(p))
                if self.pdf.pageCount()==0:raise RuntimeError('PDFを読み込めません: '+str(error))
                self.pdf_page=0;self.show_pdf();return
            pix=QPixmap(str(p))
            if not pix.isNull():
                self.stack.setCurrentWidget(self.scroll)
                if p.suffix.lower()=='.gif':
                    self.movie=QMovie(str(p));self.image.setMovie(self.movie);self.movie.start()
                else:
                    self.source_pixmap=pix;self.image.setPixmap(pix.scaled(max(1,self.scroll.viewport().width()-10),max(1,self.scroll.viewport().height()-10),Qt.KeepAspectRatio,Qt.SmoothTransformation))
                self.status.setText('画像プレビュー');return
            self.text.setPlainText(read_content(p));self.stack.setCurrentWidget(self.text)
            # Keep the existing image fallback useful to old I/F users and tests.
            self.image.setText('画像として表示できません\n'+str(p));self.status.setText('本文・一覧の簡易プレビュー')
        except Exception as exc:self.text.setPlainText(str(exc)+'\n'+str(p));self.stack.setCurrentWidget(self.text);self.status.setText('プレビューを確認してください')
    def showEvent(self,event):
        super().showEvent(event)
        paths=self.current_paths()
        if paths and paths[0].suffix.lower() in MEDIA and self.player and self.player.source().isEmpty():self.show_file()
    def resizeEvent(self,event):
        super().resizeEvent(event)
        if getattr(self,'source_pixmap',None) is not None:
            self.image.setPixmap(self.source_pixmap.scaled(max(1,self.scroll.viewport().width()-10),max(1,self.scroll.viewport().height()-10),Qt.KeepAspectRatio,Qt.SmoothTransformation))
    def show_pdf(self):
        self.stack.setCurrentWidget(self.scroll);image=self.pdf.render(self.pdf_page,QSize(max(1,self.scroll.viewport().width()-10),max(1,self.scroll.viewport().height()-10)))
        self.image.setPixmap(QPixmap.fromImage(image));self.status.setText(f'PDF {self.pdf_page+1} / {self.pdf.pageCount()}ページ')
        self.pdf_prev.setEnabled(self.pdf_page>0);self.pdf_next.setEnabled(self.pdf_page+1<self.pdf.pageCount())
    def step_pdf(self,delta):
        if self.pdf and 0<=self.pdf_page+delta<self.pdf.pageCount():self.pdf_page+=delta;self.show_pdf()
    def set_duration(self,value):self.duration=value;self.set_position(self.player.position() if self.player else 0)
    def set_position(self,value):
        if not self.seek.isSliderDown():
            self.seek.blockSignals(True);self.seek.setValue(int(value/self.duration*10000) if self.duration else 0);self.seek.blockSignals(False)
        def fmt(ms):seconds=ms//1000;return f'{seconds//60}:{seconds%60:02}'
        self.time.setText(fmt(value)+' / '+fmt(self.duration))
    def seek_to(self,value):
        if self.playback:self.playback.seek_ms(int(value/10000*self.duration))
    def play_media(self):
        if self.playback:self.playback.play()
    def pause_media(self):
        if self.playback:self.playback.pause()
    def stop_media(self):
        if self.playback:self.playback.stop()
    def closeEvent(self,event):self.release();super().closeEvent(event)

def main():
    import sys
    from .interface import PreviewInterface
    app=QApplication(sys.argv);port=PreviewInterface();w=port.create_widget();w.show();app.aboutToQuit.connect(port.shutdown);sys.exit(app.exec())
if __name__=='__main__':main()
