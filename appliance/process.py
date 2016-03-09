__author__ = 'pavle'

# https://docs.python.org/3.5/library/subprocess.html

class Process:
    
    def __init__(self, id, name, args=None):
        self.name = name
        self.id = id
        self.args = args
        
    def execute(self):
        pass
        
    def send_signal(self, signal):
        pass


class LocalProcess(Process):
    pass
    

class RemoteProcess(Process):
    pass

