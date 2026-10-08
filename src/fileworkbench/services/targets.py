"""Qt-independent selection sharing policy, reusable in other apps."""
from dataclasses import dataclass,field
from typing import Protocol

@dataclass
class TargetSet:
    paths:list[str]=field(default_factory=list)
    source:str='shared'

class TargetPolicyPort(Protocol):
    def set_targets(self,paths,source='shared'): ...
    def use_shared(self,module_id,enabled): ...
    def is_shared(self,module_id): ...

class SharedTargetPolicy:
    def __init__(self):self.targets=TargetSet();self.modes={'preview':True};self.has_targets=False
    def set_targets(self,paths,source='shared'):
        if not isinstance(paths,list) or any(not isinstance(p,str) for p in paths):raise ValueError('対象はパス文字列のリストで指定してください')
        self.targets=TargetSet(list(paths),source);self.has_targets=True
    def use_shared(self,module_id,enabled):self.modes[module_id]=bool(enabled)
    def is_shared(self,module_id):return self.modes.get(module_id,False)
