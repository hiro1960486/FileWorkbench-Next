from test_support import isolate_test_environment
isolate_test_environment()
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import unittest,tempfile
from pathlib import Path
from PySide6.QtWidgets import QApplication,QWidget
from PySide6.QtGui import QImage,QColor
from fileworkbench.module_registry import create_ports
from fileworkbench.interfaces import EventBus,ContextRouter,ModuleContext,ModuleEvent,ModuleBox
from fileworkbench.app import App
from fileworkbench.developer.workbench import DeveloperWorkbench
APP=QApplication.instance() or QApplication([])

class LinkTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        for name,color in [('a.png','red'),('b.png','blue')]:
            img=QImage(16,16,QImage.Format_RGB32);img.fill(QColor(color));img.save(str(self.root/name))
        (self.root/'folder').mkdir();(self.root/'text.txt').write_text('sample')
        self.ports=create_ports();self.bus=EventBus();self.events=[]
        self.bus.subscribe_all(self.events.append)
        for port in self.ports.values():port.subscribe(self.bus.publish)
        self.router=ContextRouter(self.bus,self.ports)
    def tearDown(self):
        for port in self.ports.values():port.shutdown()
        APP.processEvents();self.tmp.cleanup()
    def select(self,name):
        tree=self.ports['tree'].create_widget();tree.load(self.root)
        root=tree.tree.topLevelItem(0)
        item=next(root.child(i) for i in range(root.childCount()) if root.child(i).text(0)==name)
        tree.tree.setCurrentItem(item);APP.processEvents()
    def test_contracts_and_boxes(self):
        for port in self.ports.values():
            for attr in ('descriptor','create_widget','receive_context','current_context','execute','subscribe','shutdown'):
                self.assertTrue(hasattr(port,attr))
            box=ModuleBox(port);box.show();APP.processEvents();self.assertIsInstance(port.create_widget(),QWidget);box.close()
    def test_selection_replaces_image(self):
        for name in ('a.png','b.png'):
            self.select(name);p=self.ports['preview'];self.assertEqual(p.current_context().selected_paths,[str(self.root/name)])
            self.assertEqual(p.current_context().source_module,'tree');self.assertEqual(p.widget.index,0)
            self.assertFalse(p.widget.image.pixmap().isNull());self.assertEqual(p.widget.image.toolTip(),str(self.root/name))
        self.assertTrue(any(e.name=='selection.changed' and e.source=='tree' for e in self.events))
        self.assertTrue(any(e.name=='context.received' and e.source=='preview' for e in self.events))
        self.assertTrue(any(e.name=='context.routed' for e in self.events))
    def test_folder_root_and_clear(self):
        self.select('a.png');self.select('folder');self.assertEqual(self.ports['preview'].widget.index,-1)
        tree=self.ports['tree'].widget;tree.tree.setCurrentItem(tree.tree.topLevelItem(0))
        self.assertEqual(self.ports['preview'].current_context().selected_paths,[str(self.root)])
        tree.tree.clearSelection();self.assertEqual(self.ports['preview'].current_context().selected_paths,[])
        self.assertEqual(self.ports['preview'].widget.count.text(),'0 / 0')
    def test_multiple_missing_text_and_navigation(self):
        p=self.ports['preview'];p.receive_context(ModuleContext(selected_paths=[str(self.root/'a.png'),str(self.root/'b.png')]))
        p.execute('next');self.assertEqual(p.widget.index,1);p.execute('previous');self.assertEqual(p.widget.index,0)
        p.receive_context(ModuleContext(selected_paths=[str(self.root/'missing')]))
        self.assertEqual(p.widget.index,-1);self.select('text.txt');self.assertIn('text.txt',p.widget.image.text())
    def test_no_loop_and_invalid_payload(self):
        self.bus.publish(ModuleEvent('selection.changed','preview',{'selected_paths':[]}));self.assertIsNone(self.ports['preview'].widget)
        self.bus.publish(ModuleEvent('selection.changed','tree',{'selected_paths':'invalid'}))
        self.assertTrue(any(e.name=='module.error' for e in self.events))
    def test_user_and_developer_modes(self):
        for cls in (App,DeveloperWorkbench):
            window=cls();window.show();APP.processEvents()
            try:
                if isinstance(window,DeveloperWorkbench):
                    window.list.setCurrentRow(0);window.embed_selected();window.open_standalone()
                tree=window.ports['tree'].create_widget();tree.load(self.root)
                root=tree.tree.topLevelItem(0);item=next(root.child(i) for i in range(root.childCount()) if root.child(i).text(0)=='a.png')
                tree.tree.setCurrentItem(item);APP.processEvents()
                self.assertEqual(window.ports['preview'].widget.image.toolTip(),str(self.root/'a.png'))
                if isinstance(window,DeveloperWorkbench):
                    window.list.setCurrentRow(2);window.embed_selected();APP.processEvents()
                    self.assertIn('宛先=preview',window.log.toPlainText());self.assertIn('context.routed',window.log.toPlainText())
            finally:window.close();APP.processEvents()
if __name__=='__main__':unittest.main()
