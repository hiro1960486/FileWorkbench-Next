from test_support import isolate_test_environment
isolate_test_environment()
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import importlib.util,json,tempfile,unittest,subprocess,sys
from pathlib import Path
from unittest.mock import patch
from PySide6.QtWidgets import QApplication,QWidget
from fileworkbench.module_registry import create_ports,discover_manifests,descriptor_for,UnavailableModule
from fileworkbench.interfaces import ModuleContext,ModuleEvent,EventBus
from fileworkbench.developer.workbench import DeveloperWorkbench
from fileworkbench.app import App
APP=QApplication.instance() or QApplication([])
ROOT=Path(__file__).resolve().parents[1]

class ArchitectureTests(unittest.TestCase):
    def setUp(self):self.ports=create_ports();self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
    def tearDown(self):
        for p in self.ports.values():p.shutdown()
        APP.processEvents();self.tmp.cleanup()
    def test_manifests_commands_and_descriptors(self):
        for mid,data in discover_manifests().items():
            p=self.ports[mid];self.assertFalse(hasattr(p,'error'))
            self.assertEqual(p.descriptor,descriptor_for(mid));self.assertEqual(set(data['commands']),set(p.commands))
            self.assertEqual(tuple(data['emitted_events']),p.descriptor.emitted_events)
    def test_import_failure_isolated_in_both_modes(self):
        import fileworkbench.module_registry as registry
        original=registry.importlib.import_module
        def load(name,*args,**kwargs):
            if name.endswith('preview.interface'):raise ModuleNotFoundError('test missing preview dependency')
            return original(name,*args,**kwargs)
        with patch.object(registry.importlib,'import_module',side_effect=load):
            for cls in (App,DeveloperWorkbench):
                window=cls();window.show();APP.processEvents()
                self.assertIsInstance(window.ports['preview'],UnavailableModule)
                self.assertNotIsInstance(window.ports['tree'],UnavailableModule)
                window.ports['tree'].create_widget().load(self.root)
                window.close();APP.processEvents()
    def test_registry_import_has_no_domain_imports(self):
        code="import sys;import fileworkbench.module_registry;assert not any(k.startswith('fileworkbench.modules.') for k in sys.modules)"
        result=subprocess.run([sys.executable,'-c',code],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
    def test_context_copies_and_errors(self):
        p=self.ports['preview'];context=ModuleContext(options={'a':[1]});p.receive_context(context)
        context.options['a'].append(2);returned=p.current_context();returned.options['a'].append(3)
        self.assertEqual(p.current_context().options,{'a':[1]})
        with self.assertRaises(ValueError):p.receive_context(ModuleContext(selected_paths='bad'))
        for command in ('shutdown','deleteLater','setParent','nonexistent'):
            with self.assertRaises(ValueError):p.execute(command)
    def test_explicit_rename_and_compare_inputs(self):
        (self.root/'left').mkdir();(self.root/'right').mkdir()
        file=self.root/'left/a.txt';file.write_text('a')
        rename=self.ports['rename'];rename.receive_context(ModuleContext(selected_paths=[str(self.root/'left')]))
        self.assertEqual(rename.widget.files,[file]);self.assertEqual(rename.widget.table.rowCount(),1)
        compare=self.ports['compare'];compare.receive_context(ModuleContext(options={'left_folder':str(self.root/'left'),'right_folder':str(self.root/'right')}))
        compare.execute('compare');self.assertEqual(compare.widget.rows[0][3],'左のみ')
    def test_hash_context_no_dialog_or_scan(self):
        port=self.ports['hash'];port.receive_context(ModuleContext(selected_paths=[str(self.root)]))
        self.assertEqual(port.widget.input_root,self.root);self.assertEqual(port.widget.records,[])
        p=self.root/'a.txt';p.write_text('a')
        with self.assertRaises(ValueError):port.receive_context(ModuleContext(selected_paths=[str(p)]))
        self.assertEqual(port.current_context().selected_paths,[str(self.root)])
    def test_shutdown_recreate_and_subscriptions(self):
        for port in self.ports.values():
            events=[];port.subscribe(events.append);port.subscribe(events.append)
            widget=port.create_widget();port.emit('context.received');self.assertEqual(len(events),1)
            port.unsubscribe(events.append);port.emit('context.received');self.assertEqual(len(events),1)
            port.shutdown();port.shutdown();self.assertIsNone(port.widget)
            self.assertIsInstance(port.create_widget(),QWidget)
    def test_no_duplicate_boxes_and_detach_target(self):
        w=DeveloperWorkbench()
        try:
            w.list.setCurrentRow(0);w.embed_selected();box=w.boxes['tree'];w.embed_selected()
            self.assertEqual(len(w.boxes),1)
            w.list.setCurrentRow(2);box.detached.emit('tree');APP.processEvents()
            self.assertTrue(w.ports['tree'].widget.isWindow())
            self.assertIsNone(w.ports['preview'].widget)
            w.list.setCurrentRow(0);w.embed_selected();self.assertFalse(w.ports['tree'].widget.isWindow())
            self.assertEqual(len(w.boxes),1)
        finally:w.close();APP.processEvents()
    def test_event_log_order(self):
        bus=EventBus();events=[];bus.subscribe_all(lambda e:events.append(e.name))
        bus.subscribe('selection.changed',lambda e:bus.publish(ModuleEvent('context.received','preview')))
        bus.publish(ModuleEvent('selection.changed','tree'));self.assertEqual(events,['selection.changed','context.received'])
    def test_build_paths_and_release_package(self):
        def load(name):
            spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/f'{name}.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
        build=load('build_windows');self.assertEqual(build.ROOT,ROOT)
        arguments=build.pyinstaller_arguments('python');self.assertIn('--collect-submodules',arguments)
        self.assertEqual(arguments[-1],str(ROOT/'app_main.py'))
        for mid in self.ports:self.assertIn(str(ROOT/f'src/fileworkbench/modules/{mid}/module.json')+';fileworkbench/modules/'+mid,arguments)
        package=load('package_release');(self.root/'dist').mkdir();(self.root/'dist/FileWorkbench_Next.exe').write_bytes(b'test fixture')
        (self.root/'docs').mkdir();(self.root/'README.txt').write_text('readme');(self.root/'LICENSE.txt').write_text('license')
        archive=package.package(self.root)
        import zipfile,hashlib
        with zipfile.ZipFile(archive) as z:
            self.assertIsNone(z.testzip());self.assertIn('SHA256_EXE.txt',z.namelist())
        self.assertIn(hashlib.sha256(archive.read_bytes()).hexdigest(),(self.root/'release/SHA256_RELEASE.txt').read_text())
if __name__=='__main__':unittest.main()
