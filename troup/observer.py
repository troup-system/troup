
class Observable:
    
    def __init__(self):
        self.listeners = {}
    
    def on(self, event, handler):
        listeners = self.listeners.get(event)
        if not listeners:
            listeners = self.listeners[event] = []
        listeners.append(handler)
    
    def trigger(self, event, *args):
        listeners = self.listeners.get(event)
        if listeners:
            for listener in listeners:
                listener(*args)
    
    def remove_listener(self, event, listener):
        listeners = self.listeners.get(event)
        if listeners:
            listeners.remove(listener)
