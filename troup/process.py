__author__ = 'pavle'

# https://docs.python.org/3.5/library/subprocess.html


from subprocess import Popen, PIPE
from os import path, getpid, remove
import json
import logging


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

    def kill(self):
        self.process.kill()


class SSHRemoteProcess(LocalProcess):
    def __init__(self, id, name, args=None, cwd=None, forward_video=False, forward_audio=False,
                 compress_stream=False, target_host=None, target_port="22", ssh_user=''):
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

        return args + ['-f', '-p', self.target_port, '%s@%s' % (self.ssh_user, self.target_host)]


class RemoteProcess(Process):
    pass


# Proces lockfiles and IPC

class LockFile:

    def __init__(self, path, content=None, create=False, read_only=False):
        self.path = path
        self._content = content
        self.create_new = create
        self.file = None
        self.read_only = read_only
        self.__open()
        if create and content is not None:
            self.__write_content()

    def __write_content(self):
        self.file.seek(0)
        self.file.write(self._content)
        self.file.flush()

    def __open(self):
        if not self.exists():
            if not self.create_new:
                raise Exception('Lock file not found %s' % self.path)
            if not self.read_only:
                self.file = open(self.path, 'w')
        else:
            if self.create_new:
                raise Exception('Lock file already exists')
            self.file = open(self.path)

    def exists(self):
        return path.isfile(self.path)

    @property
    def content(self, value=None):
        if not self.file:
            raise Exception('Lock file not open')
        return self.file.read()

    @content.setter
    def content(self, value):
        if not self.file:
            raise Exception('Lock file not open')
        if self.read_only:
            raise Exception('Read-only file')
        self._content = value
        self.__write_content()


    def __del__(self):
        try:
            if self.file:
                self.file.close()
        except:
            pass

    def unlock(self):
        if self.path:
            remove(self.path)


class ProcessInfoFile(LockFile):

    def __init__(self, path, pid=None, create=False, with_info=None, read_only=False):
        self.pid = pid
        self.info = with_info or {}
        super(ProcessInfoFile, self).__init__(path=path, content=self.__generate_file_content(), create=create, read_only=read_only)

        if not create:
            self.__parse_file_content()

    def __generate_file_content(self):
        return '%d\n%s' % (self.pid or -1, json.dumps(self.info))

    def __parse_file_content(self):
        cnt = self.content.splitlines()
        self.pid = int(cnt[0])
        self.info = json.loads(cnt[1])

    def set_info(self, name, info):
        self.info[name] = info
        self.content = self.__generate_file_content()

    def get_info(self, name):
        return self.info.get(name)


def this_process_info_file(path, info=None, create=False):
    pid = getpid()
    try:
        return ProcessInfoFile(path=path, pid=pid, create=False)
    except Exception as e:
        if not create:
            raise e
        return ProcessInfoFile(path=path, pid=pid, create=True, with_info=info)


def open_process_lock_file(path, read_only=False):
    try:
        return ProcessInfoFile(path=path, create=False, read_only=read_only)
    except Exception as e:
        #logging.exception(e)
        return False
