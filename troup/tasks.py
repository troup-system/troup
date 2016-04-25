from uuid import uuid4


class TaskRunner:
    
    CREATED = 'CREATED'
    RUNNING = 'RUNNING'
    STOPPING = 'STOPPING'
    DONE = 'DONE'
    ERROR = 'ERROR'
    
    def __init__(self, task):
        self.task = task
        self.status = TaskRunner.CREATED
        self.result = None
        self.error = None
        
    def start(self):
        pass
    
    def stop(self, reason):
        pass


class Task:
    def __init__(self, task_id):
        self.id = task_id or str(uuid4())
    
    def run(self, context):
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
        result = self.exec(task_globasl, task_locals)
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
        self.fn_args=fn_args
        
    def __build_function__(self, fn_locals, fn_globals):
        pass

    def exec(self, fn_locals, fn_globals):
        self.function = self.__build_function__()

