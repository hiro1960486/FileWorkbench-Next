import importlib
import sys
import json
from pathlib import Path
from .interfaces import ModuleDescriptor

MODULES_DIRECTORY = Path(getattr(sys,'_MEIPASS',Path(__file__).parents[1])) / 'fileworkbench/modules'
MODULE_ORDER = ('tree','rename','preview','compare','hash','recycle')


def discover_manifests():
    result={}
    for path in sorted(MODULES_DIRECTORY.glob('*/module.json')):
        try:
            data=json.loads(path.read_text(encoding='utf-8'))
            if data['id'] != path.parent.name:raise ValueError('module id mismatch')
            result[data['id']]=data
        except Exception as exc:
            result[path.parent.name]={'id':path.parent.name,'name':path.parent.name,'error':str(exc)}
    return result


def descriptor_for(module_id):
    data=discover_manifests()[module_id]
    if 'error' in data:raise ValueError(data['error'])
    return ModuleDescriptor(data['id'],data['name'],data['version'],data['icon'],
        data.get('description',data['name']),tuple(data['capabilities']),
        tuple(data['accepted_inputs']),tuple(data['emitted_events']),tuple(data['commands']))


class UnavailableModule:
    """Keep unavailable modules visible and diagnosable without importing their UI."""
    def __init__(self,module_id,message):
        self.descriptor=ModuleDescriptor(module_id,module_id+'（利用不可）','-','','読込失敗: '+message)
        self.error=message;self.widget=None
    def create_widget(self,parent=None):
        from PySide6.QtWidgets import QLabel
        if self.widget is None:
            self.widget=QLabel('このモジュールは利用できません。\n'+self.error,parent)
            self.widget.setWordWrap(True)
        return self.widget
    def subscribe(self,callback):pass
    def unsubscribe(self,callback):pass
    def receive_context(self,context):raise RuntimeError(self.error)
    def current_context(self):
        from .interfaces import ModuleContext
        return ModuleContext()
    def execute(self,command,payload=None):raise RuntimeError(self.error)
    def shutdown(self):
        if self.widget is not None:self.widget.close();self.widget.deleteLater();self.widget=None


def create_port(module_id):
    try:
        data=discover_manifests()[module_id]
        if 'error' in data:raise ValueError(data['error'])
        module=importlib.import_module(data['interface_entrypoint'])
        port=getattr(module,module_id.capitalize()+'Interface')()
        if port.descriptor!=descriptor_for(module_id):raise ValueError('Descriptor mismatch')
        return port
    except Exception as exc:return UnavailableModule(module_id,f'{type(exc).__name__}: {exc}')


def create_ports():
    manifests=discover_manifests()
    ids=[mid for mid in MODULE_ORDER if mid in manifests]+sorted(set(manifests)-set(MODULE_ORDER))
    return {mid:create_port(mid) for mid in ids}
