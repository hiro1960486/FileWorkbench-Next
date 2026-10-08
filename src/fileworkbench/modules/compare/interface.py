from pathlib import Path
from ...interfaces import WidgetModuleAdapter
from ...module_registry import descriptor_for
from .module import CompareModule

DESCRIPTOR=descriptor_for('compare')

class CompareInterface(WidgetModuleAdapter):
    def __init__(self):
        super().__init__(DESCRIPTOR,CompareModule)
    commands = {
        'refresh': lambda w,p:w.compare() if w.left_root and w.right_root else None,
        'compare': lambda w,p: w.compare(),
        'filter': lambda w,p: w.search.setText(p.get('text','')),
    }
    def apply_context(self,widget,context):
        left=context.options.get('left_path',context.options.get('left_folder'))
        right=context.options.get('right_path',context.options.get('right_folder'))
        if left is None and context.selected_paths:left=context.selected_paths[0]
        if right is None and len(context.selected_paths)>1:right=context.selected_paths[1]
        for path in (left,right):
            if path and not Path(path).exists():raise ValueError('比較対象が存在しません')
        widget.left_root=Path(left) if left else None
        widget.right_root=Path(right) if right else None
        widget.left_path.setText(str(widget.left_root or ''));widget.right_path.setText(str(widget.right_root or ''))
        widget.rows=[];widget.render()
