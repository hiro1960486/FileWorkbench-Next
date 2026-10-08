"""Reusable playback boundary; the UI and seek slider stay in the calling app."""
from typing import Protocol

class PlaybackPort(Protocol):
    def load(self,path): ...
    def play(self): ...
    def pause(self): ...
    def stop(self): ...
    def seek_ms(self,position): ...
    def close(self): ...

class QtPlaybackService:
    def __init__(self,parent=None,video_output=None):
        from PySide6.QtMultimedia import QMediaPlayer,QAudioOutput
        self.player=QMediaPlayer(parent);self.audio=QAudioOutput(parent)
        self.player.setAudioOutput(self.audio)
        if video_output is not None:self.player.setVideoOutput(video_output)
    def load(self,path):
        from pathlib import Path
        from PySide6.QtCore import QUrl
        self.player.stop();self.player.setSource(QUrl.fromLocalFile(str(Path(path).absolute())))
    def play(self):self.player.play()
    def pause(self):self.player.pause()
    def stop(self):self.player.stop()
    def seek_ms(self,position):
        if self.player.isSeekable():self.player.setPosition(max(0,min(int(position),self.player.duration())))
    def close(self):
        from PySide6.QtCore import QUrl
        self.player.stop();self.player.setSource(QUrl())
