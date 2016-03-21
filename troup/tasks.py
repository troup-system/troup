


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
