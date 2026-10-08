from pathlib import Path
from ...interfaces import WidgetModuleAdapter
from ...module_registry import descriptor_for
from .module import TreeModule

DESCRIPTOR=descriptor_for('tree')

class TreeInterface(WidgetModuleAdapter):
    def __init__(self):
        super().__init__(DESCRIPTOR,TreeModule)
    commands = {
        'refresh': lambda w,p: w.load(w.root) if w.root else None,
        'scan': lambda w,p: w.load(Path(p['root'])) if 'root' in p else w.choose(),
        'export': lambda w,p: w.export(),
        'filter': lambda w,p: w.search.setText(p.get('text','')),
    }
    def connect_widget(self,widget):
        super().connect_widget(widget)
        widget.selection_changed.connect(lambda paths:self.emit('selection.changed',{'selected_paths':paths}))
    def apply_context(self,widget,context):
        target=context.selected_paths[0] if context.selected_paths else context.working_directory
        if target:
            path=Path(target)
            root=path if path.is_dir() else path.parent
            if not root.is_dir():raise ValueError('対象フォルダーが存在しません')
            widget.load(root)
        else:
            widget.tree.clear();widget.records=[];widget.root=None;widget.path.clear()
