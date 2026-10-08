from test_support import isolate_test_environment
isolate_test_environment()
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import unittest,tempfile
from pathlib import Path
from PySide6.QtWidgets import QApplication,QHeaderView
from fileworkbench.app import App
from fileworkbench.interfaces import ModuleContext
APP=QApplication.instance() or QApplication([])

class SharedTargetsTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.a=self.root/'a.txt';self.a.write_text('a');self.b=self.root/'b.txt';self.b.write_text('b')
        self.window=App()
    def tearDown(self):self.window.close();APP.processEvents();self.tmp.cleanup()
    def test_share_toggle_and_restore_individual(self):
        port=self.window.ports['rename'];port.receive_context(ModuleContext(selected_paths=[str(self.a)]))
        self.window.router.update_shared([str(self.b)])
        self.assertEqual(port.widget.files,[self.a])
        self.window.boxes['rename'].shared.setChecked(True);self.assertEqual(port.widget.files,[self.b])
        self.window.boxes['rename'].shared.setChecked(False);self.assertEqual(port.widget.files,[self.a])
    def test_explicit_drop_switches_to_individual(self):
        self.window.router.update_shared([str(self.a)]);self.window.boxes['rename'].shared.setChecked(True)
        self.window.ports['rename'].widget.input_paths([str(self.b)])
        self.assertFalse(self.window.boxes['rename'].shared.isChecked())
        self.window.router.update_shared([str(self.a)]);self.assertEqual(self.window.ports['rename'].widget.files,[self.b])
    def test_shared_tree_does_not_loop(self):
        self.window.boxes['tree'].shared.setChecked(True)
        self.window.router.update_shared([str(self.root)])
        self.assertEqual(self.window.ports['tree'].widget.root,self.root)
        self.assertEqual(self.window.router.policy.targets.paths,[str(self.root)])
    def test_all_columns_can_resize(self):
        for mid in ('tree','rename','compare','hash','recycle'):
            widget=self.window.ports[mid].widget;views=[widget.tree] if mid=='tree' else [widget.table]
            if mid=='recycle':views.append(widget.history_table)
            for view in views:
                header=view.header() if mid=='tree' else view.horizontalHeader()
                for column in range(header.count()):
                    self.assertEqual(header.sectionResizeMode(column),QHeaderView.Interactive)
                    header.resizeSection(column,160+column);self.assertEqual(header.sectionSize(column),160+column)
    def test_tree_filter_retains_ancestors(self):
        nested=self.root/'folder';nested.mkdir();(nested/'needle.txt').write_text('x')
        tree=self.window.ports['tree'].widget;tree.load(self.root);tree.filter('needle')
        self.assertFalse(tree.tree.topLevelItem(0).isHidden())
        root=tree.tree.topLevelItem(0);folder=next(root.child(i) for i in range(root.childCount()) if root.child(i).text(0)=='folder')
        self.assertFalse(folder.isHidden());self.assertFalse(folder.child(0).isHidden())
if __name__=='__main__':unittest.main()
