from pathlib import Path
from ...interfaces import WidgetModuleAdapter
from ...module_registry import descriptor_for
from .module import PreviewModule

DESCRIPTOR=descriptor_for('preview')

class PreviewInterface(WidgetModuleAdapter):
    def __init__(self):
        super().__init__(DESCRIPTOR,PreviewModule)
    commands = {
        'release': lambda w,p: w.release(),
        'play': lambda w,p: w.play_media(),
        'pause': lambda w,p: w.pause_media(),
        'stop': lambda w,p: w.stop_media(),
        'seek': lambda w,p: w.seek_to(int(p.get('value',0))),
        'refresh': lambda w,p: w.show_file() if 0<=w.index<len(w.files) else None,
        'next': lambda w,p: w.step(1),
        'previous': lambda w,p: w.step(-1),
    }
    def apply_context(self,widget,context):
        paths=[]
        for value in context.selected_paths:
            path=Path(value)
            if context.source_module=='drop' and path.is_dir():paths.extend(str(p) for p in sorted(path.iterdir()) if p.is_file())
            else:paths.append(value)
        widget.set_files(paths)

    def current_context(self):
        context=super().current_context()
        if self.widget is not None and self.widget.files:context.selected_paths=[str(p) for p in self.widget.files]
        return context
