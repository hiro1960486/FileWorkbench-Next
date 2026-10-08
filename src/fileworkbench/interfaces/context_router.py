from pathlib import Path
from ..services.targets import SharedTargetPolicy
from .contracts import ModuleContext, ModuleEvent

class ContextRouter:
    """Shell routing only; never accesses another module's widget."""
    def __init__(self,bus,ports):
        self.bus=bus;self.ports=ports;self.policy=SharedTargetPolicy();self.saved_individual={};self.delivering=False
        bus.subscribe('selection.changed',self.route_selection)
        bus.subscribe('target.individual_requested',lambda e:self.set_shared_mode(e.source,False))
        bus.subscribe('preview.requested',self.route_preview)
        bus.subscribe('rename.requested',self.route_rename)
        bus.subscribe('files.will_change',self.release_preview)
        bus.subscribe('files.changed',self.invalidate_preview)
    def route_rename(self,event):
        if 'rename' in self.ports:
            self.set_shared_mode('rename',False)
            try:self.ports['rename'].receive_context(ModuleContext(selected_paths=list(event.payload.get('selected_paths',[])),source_module=event.source))
            except Exception as exc:self.bus.publish(ModuleEvent('module.error','router',{'destination':'rename','message':str(exc)}))
    def set_shared_mode(self,module_id,enabled):
        if enabled and not self.policy.is_shared(module_id):self.saved_individual[module_id]=self.ports[module_id].current_context()
        self.policy.use_shared(module_id,enabled)
        self.bus.publish(ModuleEvent('target.mode_changed','router',{'module_id':module_id,'shared':bool(enabled)}))
        if enabled and self.policy.has_targets:self.deliver_shared(module_id)
        elif not enabled and module_id in self.saved_individual:
            self.delivering=True
            try:self.ports[module_id].receive_context(self.saved_individual.pop(module_id))
            except Exception as exc:self.bus.publish(ModuleEvent('module.error','router',{'destination':module_id,'message':str(exc)}))
            finally:self.delivering=False
    def update_shared(self,paths,source='shared'):
        if self.delivering:return
        try:self.policy.set_targets(paths,source)
        except Exception as exc:
            self.bus.publish(ModuleEvent('module.error','router',{'message':str(exc)}));return
        self.bus.publish(ModuleEvent('target.shared_changed','router',{'selected_paths':list(paths),'source_module':source}))
        for mid in self.ports:
            if self.policy.is_shared(mid) and mid!=source:self.deliver_shared(mid)
    def deliver_shared(self,module_id):
        if module_id not in self.saved_individual:self.saved_individual[module_id]=self.ports[module_id].current_context()
        self.delivering=True
        try:
            self.ports[module_id].receive_context(ModuleContext(selected_paths=list(self.policy.targets.paths),source_module=self.policy.targets.source))
            self.bus.publish(ModuleEvent('context.routed','router',{'source_module':self.policy.targets.source,'destination':module_id,'selected_paths':list(self.policy.targets.paths)}))
        except Exception as exc:self.bus.publish(ModuleEvent('module.error','router',{'destination':module_id,'message':str(exc)}))
        finally:self.delivering=False
    def route_selection(self,event):
        if event.source=='tree' and not self.delivering:self.update_shared(event.payload.get('selected_paths',[]),'tree')
    def route_preview(self,event):
        if event.name=='preview.requested':self.set_shared_mode('preview',False)
        if 'preview' not in self.ports:return
        paths=event.payload.get('selected_paths',[])
        if not isinstance(paths,list) or any(not isinstance(p,str) for p in paths):
            self.bus.publish(ModuleEvent('module.error','router',{'destination':'preview','message':'selected_paths must be a list of strings'}));return
        try:self.ports['preview'].receive_context(ModuleContext(selected_paths=list(paths),source_module=event.source))
        except Exception as exc:
            self.bus.publish(ModuleEvent('module.error','router',{'destination':'preview','message':str(exc)}));return
        self.bus.publish(ModuleEvent('context.routed','router',{'source_module':event.source,'destination':'preview','selected_paths':list(paths)}))
    def release_preview(self,event):
        if event.payload.get('operation') not in ('move','trash','rename'):return
        port=self.ports.get('preview')
        if not port:return
        selected=[Path(p) for p in event.payload.get('selected_paths',[])]
        current=[Path(p) for p in port.current_context().selected_paths]
        if any(a==b or a in b.parents for a in selected for b in current):port.execute('release')
    def invalidate_preview(self,event):
        results=event.payload.get('results',[])
        if not any(r.get('status')=='成功' and r.get('operation') in ('move','trash','rename') for r in results):return
        for mid,port in self.ports.items():
            try:
                if mid=='preview':
                    context=port.current_context();context.selected_paths=[p for p in context.selected_paths if Path(p).is_file()]
                    port.receive_context(context)
                elif 'refresh' in port.descriptor.commands:port.execute('refresh')
            except Exception as exc:self.bus.publish(ModuleEvent('module.error','router',{'destination':mid,'message':str(exc)}))
