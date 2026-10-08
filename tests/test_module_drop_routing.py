from test_support import isolate_test_environment
isolate_test_environment()
import os,tempfile,unittest
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from pathlib import Path
from unittest.mock import patch
from PySide6.QtCore import Qt,QMimeData,QUrl,QPoint,QPointF
from PySide6.QtGui import QDragEnterEvent,QDragMoveEvent,QDropEvent
from PySide6.QtWidgets import QApplication
from fileworkbench.app import App
from fileworkbench.module_registry import create_ports
from fileworkbench.ui import PathEdit
APP=QApplication.instance() or QApplication([])

def dispatch_drop(widget,paths):
    mime=QMimeData();mime.setUrls([QUrl.fromLocalFile(str(p)) for p in paths])
    enter=QDragEnterEvent(QPoint(8,8),Qt.CopyAction,mime,Qt.LeftButton,Qt.NoModifier)
    APP.sendEvent(widget,enter)
    move=QDragMoveEvent(QPoint(12,8),Qt.CopyAction,mime,Qt.LeftButton,Qt.NoModifier)
    APP.sendEvent(widget,move)
    drop=QDropEvent(QPointF(12,8),Qt.CopyAction,mime,Qt.LeftButton,Qt.NoModifier)
    APP.sendEvent(widget,drop)
    return enter.isAccepted(),move.isAccepted(),drop.isAccepted()

class DropRoutingTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.folder=self.root/'destination';self.folder.mkdir()
        self.file=self.root/'source.txt';self.file.write_text('sample')
        self.ports=create_ports()
    def tearDown(self):
        for port in self.ports.values():port.shutdown()
        APP.processEvents();self.tmp.cleanup()
    def test_output_fields_receive_enter_move_drop_without_replacing_input(self):
        for mid in ('tree','hash','recycle'):
            w=self.ports[mid].create_widget();w.show();APP.processEvents()
            received=[];w.input_paths=lambda paths:received.append(paths)
            self.assertEqual(dispatch_drop(w.output,[self.folder]),(True,True,True),mid)
            self.assertEqual(w.output.text(),str(self.folder));self.assertEqual(received,[])
    def test_invalid_folder_drop_stays_in_field(self):
        w=self.ports['tree'].create_widget();w.show();APP.processEvents()
        w.output.setText(str(self.folder));received=[];w.input_paths=lambda paths:received.append(paths)
        with patch('fileworkbench.ui.common.QMessageBox.warning') as warning:
            self.assertEqual(dispatch_drop(w.output,[self.file]),(True,True,True));warning.assert_called_once()
        self.assertEqual(w.output.text(),str(self.folder));self.assertEqual(received,[])
    def test_compare_bottom_side_keeps_other_side(self):
        w=self.ports['compare'].create_widget();w.show();APP.processEvents()
        self.assertEqual(dispatch_drop(w.left_path,[self.file]),(True,True,True))
        self.assertEqual(w.left_root,self.file)
        self.assertEqual(dispatch_drop(w.right_path,[self.folder]),(True,True,True))
        self.assertEqual(w.left_root,self.file);self.assertEqual(w.right_root,self.folder)
    def test_hash_input_accepts_file(self):
        w=self.ports['hash'].create_widget();w.show();APP.processEvents()
        with patch.object(w,'input_paths') as received:
            self.assertEqual(dispatch_drop(w.input_path,[self.file]),(True,True,True));received.assert_called_once();self.assertEqual([Path(p) for p in received.call_args.args[0]],[self.file])
    def test_table_viewport_keeps_external_drag_move(self):
        w=self.ports['rename'].create_widget();w.show();APP.processEvents()
        with patch.object(w,'input_paths') as received:
            self.assertEqual(dispatch_drop(w.table.viewport(),[self.file]),(True,True,True));received.assert_called_once();self.assertEqual([Path(p) for p in received.call_args.args[0]],[self.file])
    def test_common_field_and_detached_output(self):
        window=App();window.show();APP.processEvents()
        try:
            self.assertEqual(dispatch_drop(window.common_path,[self.file]),(True,True,True))
            window.hosting.detach('recycle');APP.processEvents()
            w=window.ports['recycle'].widget;received=[];w.input_paths=lambda paths:received.append(paths)
            self.assertEqual(dispatch_drop(w.output,[self.folder]),(True,True,True))
            self.assertEqual(w.output.text(),str(self.folder));self.assertEqual(received,[])
        finally:window.close();APP.processEvents()

    def test_recycle_search_field_receives_folder_and_file(self):
        w=self.ports['recycle'].create_widget();w.show();APP.processEvents()
        received=[];w.input_paths=lambda paths:received.append(paths)
        self.assertEqual(dispatch_drop(w.search,[self.folder]),(True,True,True))
        self.assertEqual(w.search.text(),str(self.folder));self.assertEqual(received,[])
        self.assertEqual(dispatch_drop(w.search,[self.file]),(True,True,True))
        self.assertEqual(w.search.text(),self.file.name);self.assertEqual(received,[])
