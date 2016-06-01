
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor

from troup.process import LocalProcess, SSHRemoteProcess


class TaskException(Exception):
    pass


class TaskRunException(TaskException):
    pass


class TaskRun:
    
    CREATED = 'CREATED'
    RUNNING = 'RUNNING'
    STOPPING = 'STOPPING'
    DONE = 'DONE'
    ERROR = 'ERROR'
    
    def __init__(self, task, future=None):
        self.task = task
        self.status = TaskRun.CREATED
        self.result = None
        self.error = None
        self.future = future
        
    def start(self):
        if self.status is not TaskRun.CREATED:
            raise TaskRunException('Failed to start task: invalid Status %s' % self.status)
        try:
            self.status = TaskRun.RUNNING
            self.do_start()
            if self.status is TaskRun.RUNNING:
                self.stop()
        except Exception as e:
            self.status = TaskRun.ERROR
            self.error = e

    def stop(self, reason=None):
        if self.status is not TaskRun.RUNNING:
            raise TaskRunException('Failed to stop task: invalid Status %s' % self.status)
        self.status = TaskRun.STOPPING
        try:
            self.do_stop(reason)
            self.status = TaskRun.DONE
        except Exception as e:
            self.error = e
            self.status = TaskRun.ERROR

    def do_start(self):
        self.task.run()

    def do_stop(self, reason=None):
        self.task.stop(reason)


class TasksRunner:

    def __init__(self, max_workers=3):
        self.tasks = {}
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    def run(self, task):
        if self.tasks.get(task.id):
            raise TaskRunException('Task already running %s' % str(task))

        task_run = TaskRun(task=task)
        self.tasks[task.id] = task_run

        def start_task():
            task_run.start()

        def on_done(*args):
            if self.tasks.get(task.id):
                run = self.tasks[task.id]
                run.result = run.future.result()
                del self.tasks[task.id]

        try:
            future = self.executor.submit(start_task)
            task_run.future = future
            future.add_done_callback(on_done)
            return task_run
        except Exception as e:
            del self.tasks[task.id]
            raise TaskRunException('Failed to schedule task run for %s' % str(task)) from e

    def stop(self, task_id, wait=False, timeout=None):
        if not self.tasks.get(task_id):
            raise TaskException('No task with id %s' % task_id)
        task = self.tasks[task_id]
        try:
            task.stop()
            if wait:
                task.future.result(timeout=timeout)
        except Exception as e:
            raise TaskException('Failed to stop task %s' % str(task)) from e
        finally:
            if self.tasks.get(task_id):
                del self.tasks[task_id]

    def shutdown(self):
        self.executor.shutdown(wait=True)


class Task:
    def __init__(self, task_id=None):
        self.id = task_id or str(uuid4())
    
    def run(self, context=None):
        pass

    def stop(self, reason=None):
        pass

    def __repr__(self):
        return '<%s.%s with id %s>' %(self.__class__.__module__, self.__class__.__name__, self.id)

    def __str__(self):
        return self.__repr__()

    def __eq__(self, other):
        if other is None:
            return False
        return type(self) == type(other) and self.id == other.id

    def __hash__(self):
        return self.id.__hash__()


class CodeTask(Task):
    def __init__(self, task_id, code, exec_type, data=None):
        super(CodeTask, self).__init__(task_id)
        self.code = code
        self.type = exec_type
        self.data = data
        self.result = None
        
    def run(self, context):
        if not context.get('locals'):
            context['locals'] = {}
        if not context.get('globals'):
            context['globals'] = globals()
    
        return self.__exec__(context['locals'], context['globals'])
    
    def __exec__(self, task_globals, task_locals):
        if not task_locals.get('result'):
            task_locals['result'] = self.__set_result__
        result = self.exec(task_globals, task_locals)
        if result is not None:
            self.result = result
        return self.result
    
    def exec(self, task_globals, task_locals):
        pass
    
    def __set_result__(self, result):
        self.result = result


class FunctionBytecodeTask(CodeTask):
    
    def __init__(self, task_id, bytecode, fn_args, fn_kwargs, data):
        super(FunctionBytecodeTask, self).__init__(task_id, code=bytecode, data=data, exec_type="FunctionBytecode")
        self.fn_args = fn_args
        self.function = None
        
    def __build_function(self, fn_locals, fn_globals):
        #FunctionType()
        pass

    def exec(self, fn_locals, fn_globals):
        #self.function = self.__build_function()
        pass


class ProcessTaskException(TaskException):
    pass


class LocalProcessTask(Task):

    def __LocalProcessBuilder(self, id, data):

        executable = data['executable']
        args = data['args']
        cwd = data.get('directory')

        process = LocalProcess(id=id, name=executable, args=args, cwd=cwd)

        return process

    def __SSHProcessBuilder(self, id, data):
        executable = data['executable']
        host = data['host']
        port = data.get('port', '22')
        cwd = data.get('directory')
        forward_video = data.get('forward_video', False)
        forward_audio = data.get('forward_audio', False)
        compress_stream = data.get('compress_stream', False)
        ssh_user = data.get('ssh_user', '')

        process = SSHRemoteProcess(id=id, name=executable, cwd=cwd, target_host=host, target_port=port,
                                   forward_video=forward_video, forward_audio=forward_audio,
                                   compress_stream=compress_stream, ssh_user=ssh_user)

        return process

    PROCESS_BUILDERS = {
        'LocalProcess': __LocalProcessBuilder,
        'SSHProcess': __SSHProcessBuilder
    }

    def __init__(self, process_type, process_data, task_id=None):
        super(LocalProcessTask, self).__init__(task_id=task_id)
        self.process = None
        self.__build_process(process_type, process_data)

    def __build_process(self, process_type, process_data):
        builder = LocalProcessTask.PROCESS_BUILDERS.get(process_type)
        if not builder:
            raise ProcessTaskException('Unsupported process type %s' % process_type)
        try:
            self.process = builder(self.id, process_data)
        except Exception as e:
            raise ProcessTaskException('Failed to build process of type %s' % process_type) from e

    def run(self, context=None):
        self.process.execute()
        
    def stop(self, reason=None):
        self.process.kill()