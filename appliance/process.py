__author__ = 'pavle'

# https://docs.python.org/3.5/library/subprocess.html


from subprocess import Popen

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
    
    def __init__(self, id, name, args=None, cwd=None):
        super(self, Process).__init__(id, name, args)
        self.cwd = cwd
        self.process = None
        self.input = None
        self.output = None
        self.error = None
    

class RemoteProcess(Process):
    pass

