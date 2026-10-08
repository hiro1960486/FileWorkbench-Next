from copy import deepcopy
from .contracts import ModuleContext, ModuleEvent


class WidgetModuleAdapter:
    """Widget lifetime and event transport only; domain logic lives in interfaces."""
    commands = {}

    def __init__(self, descriptor, widget_class):
        self.descriptor = descriptor
        self.widget_class = widget_class
        self.widget = None
        self.context = ModuleContext()
        self.listeners = []

    def create_widget(self, parent=None):
        if self.widget is None:
            widget = self.widget_class()
            widget.setParent(parent)
            try:
                self.connect_widget(widget)
            except Exception:
                widget.close();widget.deleteLater()
                raise
            self.widget = widget
        return self.widget

    def connect_widget(self, widget):
        widget.bind_port(self)

    def apply_context(self, widget, context):
        raise NotImplementedError('Each module interface must implement apply_context')

    def receive_context(self, context):
        if not isinstance(context, ModuleContext):
            raise TypeError('Expected ModuleContext')
        if not isinstance(context.selected_paths, list) or any(not isinstance(p, str) for p in context.selected_paths):
            raise ValueError('selected_paths must be a list of strings')
        if not isinstance(context.options, dict):
            raise ValueError('options must be a dictionary')
        if not isinstance(context.working_directory,str) or not isinstance(context.source_module,str):
            raise ValueError('working_directory and source_module must be strings')
        candidate = deepcopy(context)
        try:
            self.apply_context(self.create_widget(), candidate)
        except Exception as exc:
            self.emit('module.error', {'message': str(exc)})
            raise
        self.context = candidate
        self.emit('context.received', {'selected_paths': list(candidate.selected_paths),
                  'options': deepcopy(candidate.options), 'source_module': candidate.source_module})

    def current_context(self):
        return deepcopy(self.context)

    def execute(self, command, payload=None):
        if command not in self.commands:
            raise ValueError(f'未対応コマンド: {command}')
        try:
            result = self.commands[command](self.create_widget(), payload or {})
        except Exception as exc:
            self.emit('module.error', {'command': command, 'message': str(exc)})
            raise
        self.emit('command.completed', {'command': command})
        return result

    def subscribe(self, callback):
        if callback not in self.listeners:
            self.listeners.append(callback)

    def unsubscribe(self, callback):
        if callback in self.listeners:
            self.listeners.remove(callback)

    def emit(self, name, payload=None):
        event = ModuleEvent(name, self.descriptor.module_id, payload or {})
        for callback in tuple(self.listeners):
            callback(event)

    def shutdown(self):
        widget, self.widget = self.widget, None
        if widget is not None:
            widget.close()
            widget.deleteLater()
