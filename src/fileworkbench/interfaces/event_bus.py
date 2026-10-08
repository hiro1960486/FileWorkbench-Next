from collections import defaultdict
from typing import Callable
from .contracts import ModuleEvent
class EventBus:
    def __init__(self): self._listeners=defaultdict(list);self._all=[]
    def subscribe(self,event_name:str,callback:Callable[[ModuleEvent],None]): self._listeners[event_name].append(callback)
    def subscribe_all(self,callback): self._all.append(callback)
    def publish(self,event:ModuleEvent):
        for callback in tuple(self._all): callback(event)
        for callback in tuple(self._listeners[event.name]): callback(event)
