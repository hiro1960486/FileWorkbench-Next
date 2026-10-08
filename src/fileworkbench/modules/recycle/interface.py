from ...interfaces import WidgetModuleAdapter
from ...module_registry import descriptor_for
from .module import RecycleModule
DESCRIPTOR=descriptor_for('recycle')
class RecycleInterface(WidgetModuleAdapter):
    commands={'search':lambda w,p:w.refresh(),'restore':lambda w,p:w.restore_selected()}
    def __init__(self):super().__init__(DESCRIPTOR,RecycleModule)
    def apply_context(self,widget,context):
        target=context.selected_paths[0] if context.selected_paths else context.working_directory
        widget.search.setText(str(target or context.options.get('query','')))
        if 'destination' in context.options:widget.output.setText(str(context.options['destination']))
