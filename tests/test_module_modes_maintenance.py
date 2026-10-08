from test_support import isolate_test_environment
isolate_test_environment()
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import unittest,tempfile
from pathlib import Path
from unittest.mock import patch
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication,QMessageBox
from fileworkbench.module_registry import create_ports
from fileworkbench.interfaces import ModuleContext
from fileworkbench.services.naming import RenameRules,build_plan
from fileworkbench.services.file_operations import FileOperationsService
from fileworkbench.developer.workbench import DeveloperWorkbench
APP=QApplication.instance() or QApplication([])
class ModeTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.ports=create_ports()
    def tearDown(self):
        for port in self.ports.values():port.shutdown()
        APP.processEvents();self.tmp.cleanup()
    def test_rename_rule_engine(self):
        a=self.root/'IMG_20.JPG';b=self.root/'IMG_10.JPG';a.write_text('a');b.write_text('b')
        rules=RenameRules(find=r'IMG_\d+',replacement='photo',regex=True,numbering=True,start=5,digits=3,date_source='modified',extension='png')
        rows=build_plan([a,b],rules);self.assertEqual(rows[0][0],b);self.assertIn('005_photo',rows[0][1].name);self.assertTrue(rows[0][1].name.endswith('.png'))
        rows=build_plan([a],RenameRules(find='[',regex=True));self.assertTrue(rows[0][2].startswith('無効:'))
        rows=build_plan([a],RenameRules(extension_filter='txt'));self.assertEqual(rows[0][2],'対象外')
    def test_light_advanced_configuration_via_if(self):
        file=self.root/'a.txt';file.write_text('a');port=self.ports['rename'];port.receive_context(ModuleContext(selected_paths=[str(file)]))
        port.execute('configure',{'numbering':True,'digits':2,'mode':'advanced'});self.assertEqual(port.widget.rows[0][1].name,'01_a.txt')
        port.widget.mode.setCurrentIndex(0);self.assertEqual(port.widget.rows[0][1].name,'a.txt')
        port.widget.mode.setCurrentIndex(1);self.assertEqual(port.widget.rows[0][1].name,'01_a.txt')
    def test_rename_selected_rows_only_and_backup(self):
        a=self.root/'a.txt';b=self.root/'b.txt';a.write_text('a');b.write_text('b');port=self.ports['rename'];port.receive_context(ModuleContext(selected_paths=[str(a),str(b)]))
        w=port.widget;w.service=FileOperationsService(self.root/'state');w.prefix.setText('new_');w.selected_only.setChecked(True)
        row=next(i for i in range(w.table.rowCount()) if w.table.item(i,0).text()==str(a));w.table.selectRow(row)
        with patch.object(QMessageBox,'question',return_value=QMessageBox.Yes),patch.object(QMessageBox,'information'):w.execute()
        self.assertTrue((self.root/'new_a.txt').exists());self.assertTrue(b.exists());self.assertFalse((self.root/'new_b.txt').exists());self.assertEqual(len(w.service.history()),1)
    def test_file_compare_and_swap(self):
        a=self.root/'a.txt';b=self.root/'b.txt';a.write_text('a');b.write_text('a');p=self.ports['compare'];p.receive_context(ModuleContext(options={'left_path':str(a),'right_path':str(b)}));p.execute('compare')
        self.assertEqual(p.widget.rows[0][3],'完全一致');p.widget.swap_targets();self.assertEqual(p.widget.left_root,b);self.assertEqual(p.widget.right_root,a)
        self.assertFalse(p.widget.left_path.folder_only);self.assertTrue(p.widget.table.dragEnabled())
    def test_numeric_sort_keeps_complete_rows(self):
        w=self.ports['hash'].create_widget();w.records=[(self.root/'large',1000,'aaa'),(self.root/'small',20,'bbb')];w.render();w.table.sortItems(1,Qt.AscendingOrder)
        self.assertEqual(w.table.item(0,0).text(),str(self.root/'small'));self.assertEqual(w.table.item(0,2).text(),'bbb')
    def test_developer_standalone_is_independent(self):
        w=DeveloperWorkbench()
        try:
            w.list.setCurrentRow(0);w.embed_selected();registered=w.ports['tree'].widget;w.open_standalone()
            self.assertIsNot(w.independent_ports[-1].widget,registered);self.assertFalse(registered.isWindow())
            data=w.diagnose();self.assertIn('PySide6',data['dependencies']);self.assertEqual(len(data['modules']),6)
        finally:w.close();APP.processEvents()
    def test_contract_test_does_not_clear_integrated_state(self):
        w=DeveloperWorkbench()
        try:
            w.list.setCurrentRow(0);port=w.ports['tree'];port.receive_context(ModuleContext(selected_paths=[str(self.root)]))
            with patch.object(QMessageBox,'information'):w.contract_test()
            self.assertEqual(port.widget.root,self.root);self.assertNotIn('NG',w.log.toPlainText())
        finally:w.close();APP.processEvents()
if __name__=='__main__':unittest.main()
