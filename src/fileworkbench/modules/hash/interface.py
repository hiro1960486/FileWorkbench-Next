from pathlib import Path
from ...interfaces import WidgetModuleAdapter
from ...module_registry import descriptor_for
from .module import HashModule

DESCRIPTOR=descriptor_for('hash')

class HashInterface(WidgetModuleAdapter):
    def __init__(self):
        super().__init__(DESCRIPTOR,HashModule)
    commands = {
        'refresh': lambda w,p:w.refresh_records(),
        'scan': lambda w,p: w.scan(Path(p['root'])) if 'root' in p else w.scan(),
        'filter': lambda w,p: w.search.setText(p.get('text','')),
        'export': lambda w,p: w.export(),
    }
    def apply_context(self,widget,context):
        target=context.selected_paths[0] if context.selected_paths else context.working_directory
        if target and not Path(target).is_dir():raise ValueError('HASH入力はフォルダーで指定してください')
        widget.input_root=Path(target) if target else None
        widget.input_path.setText(str(widget.input_root or ''));widget.status.setText('対象: '+str(widget.input_root or '未選択'))
        widget.records=[];widget.render()
