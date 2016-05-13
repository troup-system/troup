__author__ = 'pavle'

# https://docs.python.org/3.5/library/subprocess.html


from subprocess import Popen, PIPE
from os import path

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
        super(LocalProcess, self).__init__(id, name, args)
        self.cwd = cwd
        self.process = None
        self.input = None
        self.output = None
        self.error = None
    
    def execute(self):
        self.process = Popen(args=[self.name]+self.args, cwd=self.cwd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        self.input = self.process.stdin
        self.output = self.process.stdout
        self.error = self.process.stderr
    
    def wait(self):
        if self.process:
            self.process.wait()

class SSHRemoteProcess(LocalProcess):
    def __init__(self, id, name, args=None, cwd=None, forward_video=False, forward_audio=False,  compress_stream=False, target_host=None, target_port="22", ssh_user=''):
        self.forward_video = forward_video
        self.forward_audio = forward_audio
        self.compress_stream = compress_stream
        self.target_host = target_host
        self.target_port = target_port
        self.ssh_user = ssh_user
        
        self.ssh_args = self.get_ssh_args()
        args = self.ssh_args + [name] + args
        super(SSHRemoteProcess, self).__init__(id=id, name='/usr/bin/ssh', args=args, cwd=cwd)
        
    def get_ssh_args(self):
        args = []
        if self.forward_video:
            args.append('-Y')
        
        if self.compress_stream:
            args.append('-C')
        
        if not self.target_host:
            raise Exception('No target host for remote SSH process')
        
        if not self.ssh_user:
            raise Exception('No ssh user defined')
        
        return args + [ '-f', '-p', self.target_port, '%s@%s'%(self.ssh_user, self.target_host)]
    


class RemoteProcess(Process):
    pass


# Proces lockfiles and IPC

class LockFile:
    
    def __init__(self, path, content=None, create=False):
        self.path = path
        self._content = content
        self.create_new = create
        self.file = None
        self.__open()
    
    def __open(self):
        if not self.exists():
            if not self.create_new:
                raise Exception('Lock file not found %s' % self.path)
            path.touch(self.path)
        else:
            if self.create_new:
                raise Exception('Lock file already exists')
            self.file = open(self.path)
    
    def exists(self):
        return path.isFile(self.path)
    
    @property
    def content(self, value=None):
        pass



