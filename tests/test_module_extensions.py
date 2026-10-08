from test_support import isolate_test_environment,make_test_symlink
isolate_test_environment()
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import unittest,tempfile,shutil,zipfile,wave,time,json
from pathlib import Path
from unittest.mock import patch,Mock
from PySide6.QtCore import Qt,QMimeData,QUrl,QPoint
from PySide6.QtGui import QDropEvent,QImage,QColor,QDragEnterEvent
from PySide6.QtWidgets import QApplication,QAbstractItemView
from PySide6.QtTest import QTest
from fileworkbench.services.file_operations import FileOperationsService,fingerprint,copy_exclusive,normalize_selection
from fileworkbench.services.recycle_bin import WindowsRecycleBin,RecycleEntry
from fileworkbench.module_registry import create_ports
from fileworkbench.interfaces import ModuleContext
from fileworkbench.app import App
from fileworkbench.modules.preview.renderers import read_content
APP=QApplication.instance() or QApplication([])

class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.data=self.root/'data';self.data.mkdir();self.out=self.root/'out';self.out.mkdir()
        self.service=FileOperationsService(self.root/'state',trash_backend=self.fake_trash)
    def tearDown(self):self.tmp.cleanup()
    def fake_trash(self,path):
        p=Path(path);shutil.rmtree(p) if p.is_dir() else p.unlink()
    def test_copy_collision_and_folder(self):
        p=self.data/'a.txt';p.write_text('new');(self.out/'a.txt').write_text('old')
        result=self.service.perform('copy',[p],self.out)[0];self.assertEqual(result.status,'成功')
        self.assertEqual((self.out/'a.txt').read_text(),'old');self.assertEqual(Path(result.target).read_text(),'new')
        folder=self.data/'dir';folder.mkdir();(folder/'file').write_text('x')
        result=self.service.perform('copy',[folder],self.out)[0];self.assertEqual(fingerprint(folder),fingerprint(result.target))
    def test_move_trash_backup_and_restore(self):
        p=self.data/'a';p.write_text('original');result=self.service.perform('move',[p],self.out)[0]
        self.assertFalse(p.exists());self.assertEqual(Path(result.target).read_text(),'original')
        restored=self.service.restore_backup(result.history_id);self.assertEqual(Path(restored.target).read_text(),'original')
        result=self.service.perform('trash',[p])[0];self.assertFalse(p.exists());self.assertEqual(len(self.service.history()),2)
        (self.data/'a').write_text('other');restored=self.service.restore_backup(result.history_id)
        self.assertEqual((self.data/'a').read_text(),'other');self.assertEqual(Path(restored.target).read_text(),'original')
    def test_tampered_backup_refuses_restore(self):
        p=self.data/'a';p.write_text('original');result=self.service.perform('trash',[p])[0]
        entry=self.service.history()[0];Path(entry['backup']).write_text('changed')
        with self.assertRaises(ValueError):self.service.restore_backup(result.history_id)
        self.assertFalse(p.exists())
    def test_backup_failure_keeps_source(self):
        p=self.data/'a';p.write_text('original')
        with patch('fileworkbench.services.file_operations.copy_exclusive',side_effect=OSError('disk full')):
            result=self.service.perform('trash',[p])[0]
        self.assertEqual(result.status,'失敗');self.assertEqual(p.read_text(),'original')
    def test_nested_selection_destination_and_cancel(self):
        folder=self.data/'folder';folder.mkdir();child=folder/'a';child.write_text('a')
        self.assertEqual(normalize_selection([folder,child]),[folder.absolute()])
        result=self.service.perform('copy',[folder],folder)[0];self.assertEqual(result.status,'失敗')
        self.assertEqual(self.service.perform('trash',[child],cancel=lambda:True),[]);self.assertTrue(child.exists())
    def test_no_overwrite(self):
        a=self.data/'a';a.write_text('a');b=self.data/'b';b.write_text('b')
        with self.assertRaises(FileExistsError):copy_exclusive(a,b)
    def test_trash_does_not_follow_symlink(self):
        a=self.data/'a';a.write_text('a')
        link=self.data/'link'
        make_test_symlink(self,link,a)
        result=self.service.perform('trash',[link])[0]
        self.assertEqual(result.status,'失敗');self.assertTrue(a.exists());self.assertTrue(link.is_symlink())
    def test_skip_restore(self):
        p=self.data/'a';p.write_text('a');result=self.service.perform('trash',[p])[0];p.write_text('other')
        restored=self.service.restore_backup(result.history_id,collision='skip');self.assertEqual(restored.status,'スキップ');self.assertEqual(p.read_text(),'other')

class ExtensionGuiTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.ports=create_ports()
    def tearDown(self):
        for p in self.ports.values():p.shutdown()
        APP.processEvents();self.tmp.cleanup()
    def test_extended_selections_and_drop(self):
        image=self.root/'a.png';im=QImage(20,20,QImage.Format_RGB32);im.fill(QColor('red'));im.save(str(image))
        for mid in ('tree','rename','compare','hash'):
            w=self.ports[mid].create_widget();view=w.tree if mid=='tree' else w.table
            self.assertEqual(view.selectionMode(),QAbstractItemView.ExtendedSelection);self.assertTrue(view.viewport().acceptDrops())
        w=self.ports['preview'].create_widget();mime=QMimeData();mime.setUrls([QUrl.fromLocalFile(str(image))])
        event=QDropEvent(QPoint(10,10),Qt.CopyAction,mime,Qt.LeftButton,Qt.NoModifier);w.dropEvent(event)
        self.assertEqual(w.files,[image]);self.assertFalse(w.image.pixmap().isNull())
    def test_text_office_zip_metadata(self):
        text=self.root/'a.txt';text.write_bytes('日本語テスト'.encode('cp932'));self.assertEqual(read_content(text),'日本語テスト')
        text.write_bytes('UTF-8本文'.encode('utf-8'));self.assertEqual(read_content(text),'UTF-8本文')
        text.write_bytes('UTF-16本文'.encode('utf-16'));self.assertEqual(read_content(text),'UTF-16本文')
        doc=self.root/'a.docx'
        with zipfile.ZipFile(doc,'w') as z:z.writestr('word/document.xml','<w:document xmlns:w="urn:w"><w:t>本文</w:t></w:document>')
        self.assertIn('本文',read_content(doc))
        archive=self.root/'a.zip'
        with zipfile.ZipFile(archive,'w') as z:z.writestr('hello.txt','x')
        self.assertIn('hello.txt',read_content(archive))
        other=self.root/'a.unknown';other.write_bytes(b'x');self.assertIn('1 bytes',read_content(other))
    def test_pdf_render_and_navigation(self):
        p=self.root/'a.pdf'
        objects=[b'<< /Type /Catalog /Pages 2 0 R >>',b'<< /Type /Pages /Kids [3 0 R 4 0 R] /Count 2 >>',b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 200] >>',b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 200] >>']
        data=b'%PDF-1.4\n';offsets=[0]
        for i,obj in enumerate(objects,1):offsets.append(len(data));data+=str(i).encode()+b' 0 obj\n'+obj+b'\nendobj\n'
        xref=len(data);data+=b'xref\n0 5\n0000000000 65535 f \n'
        for offset in offsets[1:]:data+=f'{offset:010} 00000 n \n'.encode()
        data+=f'trailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF'.encode();p.write_bytes(data)
        port=self.ports['preview'];port.receive_context(ModuleContext(selected_paths=[str(p)]))
        self.assertEqual(port.widget.pdf.pageCount(),2);port.widget.step_pdf(1);self.assertEqual(port.widget.pdf_page,1)
        port.execute('release')
        renamed=p.with_name('released.pdf');p.rename(renamed);renamed.unlink()
    def test_seek_drag_click_and_stop_interface(self):
        w=self.ports['preview'].create_widget();self.assertIsNotNone(w.player)
        w.seek.setEnabled(True);w.seek.resize(300,30)
        with patch.object(w.player,'isSeekable',return_value=True),patch.object(w.player,'duration',return_value=100000),patch.object(w.player,'setPosition') as set_position:
            w.duration=100000;w.seek_to(7500);set_position.assert_called_with(75000)
            QTest.mouseClick(w.seek,Qt.LeftButton,Qt.NoModifier,QPoint(150,15));self.assertAlmostEqual(set_position.call_args.args[0],50000,delta=500)
        with patch.object(w.player,'play') as play,patch.object(w.player,'stop') as stop:
            self.ports['preview'].execute('play');self.ports['preview'].execute('stop');play.assert_called_once();stop.assert_called_once()
    def test_manual_preview_context_and_clear(self):
        p=self.root/'a.txt';p.write_text('abc');port=self.ports['preview'];w=port.create_widget();w.files=[p];w.index=0;w.show_file()
        self.assertEqual(port.current_context().selected_paths,[str(p)]);port.receive_context(ModuleContext());self.assertEqual(w.count.text(),'0 / 0')
    def test_detach_all_module_boxes(self):
        window=App();window.show();APP.processEvents()
        try:
            for mid in window.ports:
                window.hosting.detach(mid);self.assertIn(mid,window.hosting.windows)
                window.hosting.windows[mid].close();APP.processEvents()
                self.assertNotIn(mid,window.hosting.windows);self.assertFalse(window.ports[mid].widget.isWindow())
        finally:window.close();APP.processEvents()
    def test_recycle_filter_and_history(self):
        w=self.ports['recycle'].create_widget();w.entries=[RecycleEntry('one','a.txt',str(self.root),'2026-10-01',False),RecycleEntry('two','b.txt',str(self.root),'2026-10-06',False)]
        w.search.setText('a.txt');w.render();self.assertEqual(w.table.rowCount(),1)
        w.search.clear();w.start.setText('2026-10-05');w.render();self.assertEqual(w.table.rowCount(),1)
        w.service=FileOperationsService(self.root/'state',trash_backend=lambda p:Path(p).unlink())
        p=self.root/'file';p.write_text('a');w.service.perform('trash',[p]);w.history_entries=w.service.history();w.render_history();self.assertEqual(w.history_table.rowCount(),1)
    def test_non_windows_recycle_is_explicit(self):
        with patch('fileworkbench.services.recycle_bin.sys.platform','linux'):
            with self.assertRaisesRegex(RuntimeError,'Windows'):WindowsRecycleBin().list_entries()
class NativeShellAdapterTests(unittest.TestCase):
    def test_shell_restore_uses_item_object_and_preserves_staging(self):
        with tempfile.TemporaryDirectory() as d:
            directory=Path(d);(directory/'a.txt').write_text('existing')
            class Item:
                Path='virtual-recycle-id';Name='a.txt';IsFolder=False
                def ExtendedProperty(self,name):return str(directory) if name.endswith('DeletedFrom') else '2026-10-01'
            item=Item();items=[item]
            class Folder:
                def __init__(self,path):self.path=path
                def Items(self):return items
                def MoveHere(self,value,flags):
                    self_item=value
                    assert self_item is item
                    (Path(self.path)/item.Name).write_text('restored')
                    items.remove(item)
            class Shell:
                def NameSpace(self,path):return Folder(path)
            backend=WindowsRecycleBin()
            with patch.object(backend,'_shell',return_value=Shell()):
                listed=backend.list_entries();self.assertEqual(listed[0].original_directory,str(directory))
                result=backend.restore(item.Path,str(directory),'rename')
                self.assertEqual((directory/'a.txt').read_text(),'existing')
                self.assertEqual(Path(result.target).read_text(),'restored');self.assertEqual(items,[])
                self.assertEqual(len(list(directory.glob('.fwn_restore_*'))),1)
    def test_actual_wav_duration_and_seek(self):
        from fileworkbench.modules.preview.interface import PreviewInterface
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'test.wav'
            with wave.open(str(p),'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(8000);f.writeframes(b'\0\0'*16000)
            port=PreviewInterface()
            try:
                port.receive_context(ModuleContext(selected_paths=[str(p)]));w=port.widget
                deadline=time.monotonic()+3
                while time.monotonic()<deadline and not w.duration:APP.processEvents();time.sleep(.01)
                self.assertEqual(w.duration,2000);self.assertTrue(w.player.isSeekable());w.seek_to(5000);self.assertEqual(w.player.position(),1000)
            finally:port.shutdown();APP.processEvents()
    def test_tree_export_does_not_overwrite(self):
        from fileworkbench.core.tree_export import scan_tree,export_tree
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d);target=folder/'tree.txt';target.write_text('old')
            with self.assertRaises(FileExistsError):export_tree(scan_tree(folder),folder,target,'TXT')
            self.assertEqual(target.read_text(),'old')

if __name__=='__main__':unittest.main()

class RecycleSearchFeedbackTests(unittest.TestCase):
    def setUp(self):
        self.ports=create_ports();self.widget=self.ports['recycle'].create_widget()
    def tearDown(self):
        for port in self.ports.values():port.shutdown()
        APP.processEvents()
    def test_search_failure_is_visible(self):
        with patch.object(self.widget.service,'history',return_value=[]),patch.object(self.widget.backend,'list_entries',side_effect=RuntimeError('Shell unavailable')),patch('fileworkbench.modules.recycle.module.QMessageBox.warning') as warning:
            self.assertFalse(self.widget.refresh());warning.assert_called_once()
            self.assertIn('Shell unavailable',self.widget.status.text())
    def test_filtered_results_can_be_cleared(self):
        entry=RecycleEntry('test-id','sample.txt','C:/example','2026-10-08',False)
        self.widget.search.setText('unmatched')
        with patch.object(self.widget.service,'history',return_value=[]),patch.object(self.widget.backend,'list_entries',return_value=[entry]):
            self.assertTrue(self.widget.refresh())
        self.assertEqual(self.widget.table.rowCount(),0);self.assertIn('表示: 0件',self.widget.status.text())
        self.widget.clear_filters();self.assertEqual(self.widget.table.rowCount(),1)
    def test_history_failure_does_not_block_native_search(self):
        entry=RecycleEntry('test-id','sample.txt','C:/example','2026-10-08',False)
        with patch.object(self.widget.service,'history',side_effect=ValueError('bad history')),patch.object(self.widget.backend,'list_entries',return_value=[entry]):
            self.assertTrue(self.widget.refresh())
        self.assertEqual(self.widget.table.rowCount(),1);self.assertIn('bad history',self.widget.status.text())
