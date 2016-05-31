from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor


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
    
    def __init__(self, task):
        self.task = task
        self.status = TaskRun.CREATED
        self.result = None
        self.error = None
        
    def start(self):
        if self.status is not TaskRun.CREATED:
            raise TaskRunException('Failed to start task: invalid Status %s' % self.status)
        try:
            self.do_start()
            self.stop()
        except Exception as e:
            self.status = TaskRun.ERROR
            self.error = e

    def stop(self, reason=None):
        if self.status is not TaskRun.RUNNING:
            raise TaskRunException('Failed to start task: invalid Status %s' % self.status)
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

        def start_task():
            pass

        def on_done():
            pass

        self.tasks[task.id] = task
        try:
            future = self.executor.submit(start_task)
            future.add_done_callback(on_done)
            return future
        except Exception as e:
            del self.tasks[task.id]
            raise TaskRunException('Failed to schedule task run for %s' % str(task)) from e

    def stop(self, task_id):
        if not self.tasks.get(task_id):
            raise TaskException('No task with id %s' % task_id)
        task = self.tasks[task_id]
        try:
            task.stop()
        except Exception as e:
            raise TaskException('Failed to stop task %s' % str(task)) from e
        finally:
            del self.tasks[task_id]

    def shutdown(self):
        self.executor.shutdown(wait=True)


class Task:
    def __init__(self, task_id):
        self.id = task_id or str(uuid4())
    
    def run(self, context):
        pass

    def stop(self, reason=None):
        pass


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
        pass

    def exec(self, fn_locals, fn_globals):
        self.function = self.__build_function()