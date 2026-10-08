from pathlib import Path
from ...interfaces import WidgetModuleAdapter
from ...module_registry import descriptor_for
from .module import RenameModule

DESCRIPTOR=descriptor_for('rename')

class RenameInterface(WidgetModuleAdapter):
    def __init__(self):
        super().__init__(DESCRIPTOR,RenameModule)
    commands = {
        'configure': lambda w,p:w.configure_rules(p),
        'refresh': lambda w,p: (setattr(w,'files',[f for f in w.files if f.is_file()]),w.preview()),
        'preview': lambda w,p: w.preview(),
        'rename': lambda w,p: w.execute(),
    }
    def apply_context(self,widget,context):
        if 'rename_rules' in context.options:widget.configure_rules(context.options['rename_rules'])
        paths=[Path(p) for p in context.selected_paths]
        if not paths and context.working_directory:paths=[Path(context.working_directory)]
        files=[]
        for path in paths:
            files.extend(sorted(p for p in path.rglob('*') if p.is_file()) if path.is_dir() else [path] if path.is_file() else [])
        widget.files=list(dict.fromkeys(files));widget.preview();widget.status.setText(f'対象: {len(widget.files)}ファイル')
