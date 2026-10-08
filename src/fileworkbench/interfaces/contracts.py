from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable, Protocol
from PySide6.QtWidgets import QWidget

@dataclass(frozen=True)
class ModuleDescriptor:
    module_id: str
    display_name: str
    version: str
    icon: str
    description: str
    capabilities: tuple[str, ...] = ()
    accepted_inputs: tuple[str, ...] = ()
    emitted_events: tuple[str, ...] = ()
    commands: tuple[str, ...] = ()

@dataclass
class ModuleContext:
    selected_paths: list[str] = field(default_factory=list)
    working_directory: str = ''
    options: dict[str, Any] = field(default_factory=dict)
    source_module: str = 'shell'

@dataclass
class ModuleEvent:
    name: str
    source: str
    payload: dict[str, Any] = field(default_factory=dict)

class ModulePort(Protocol):
    descriptor: ModuleDescriptor
    def create_widget(self, parent: QWidget | None = None) -> QWidget: ...
    def receive_context(self, context: ModuleContext) -> None: ...
    def current_context(self) -> ModuleContext: ...
    def execute(self, command: str, payload: dict[str, Any] | None = None) -> Any: ...
    def subscribe(self, callback: Callable[[ModuleEvent], None]) -> None: ...
    def shutdown(self) -> None: ...
