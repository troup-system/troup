# Copyright 2016 Pavle Jonoski
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor
from threading import Thread
from collections import deque
import logging
from functools import reduce

from troup.process import LocalProcess, SSHRemoteProcess
from troup.threading import IntervalTimer
from datetime import datetime, timedelta

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
    
    def __init__(self, task, future=None, run_id=None):
        self.task = task
        self.status = TaskRun.CREATED
        self.result = None
        self.error = None
        self.future = future
        self.start_time = None
        self.ttl = task.ttl
        self.id = run_id or task.id or str(uuid4())

    def start(self):
        if self.status is not TaskRun.CREATED:
            raise TaskRunException('Failed to start task: invalid Status %s' % self.status)
        try:
            self.status = TaskRun.RUNNING
            self.start_time = datetime.now()
            self.do_start()
            if self.status is TaskRun.RUNNING:
                self.stop()
        except Exception as e:
            logging.exception('Failed to execute task')
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
            logging.exception('Failed to stop task')
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
        self.checker = IntervalTimer(1000, offset=1000, target=self._check_tasks, name='TasksRunnerMaintenanceTimer')
        self.checker.start()

    def _check_tasks(self):
        to_remove = []
        for id, task_run in self.tasks.items():
            if task_run.status is TaskRun.DONE or task_run.status is TaskRun.ERROR:
                to_remove.append(task_run)
        for task_run in to_remove:
            self.__remove_task(task_run)

    def run(self, task):
        if self.tasks.get(task.id):
            raise TaskRunException('Task already running %s' % str(task))

        task_run = TaskRun(task=task)
        self.tasks[task.id] = task_run

        def start_task():
            print('Running task [%s]' % task_run.id)
            task_run.start()
            print('Run and done - task [%s]' % task_run.id)

        def on_done(*args):
            if self.tasks.get(task.id):
                run = self.tasks[task.id]
                run.result = run.future.result()
                if not run.ttl:
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
        self.checker.cancel()
        self.executor.shutdown(wait=True)

    def __get_task(self, task_id):
        task = self.tasks.get(task_id)
        if not task:
            raise TaskException('No task with id %s' % task_id)
        return task

    def __remove_task(self, task, force=False):
        if force or not task.ttl:
            del self.tasks[task.id]
        elif task.ttl > 0:
            td = datetime.now() - task.start_time
            ttl = timedelta(microseconds=task.ttl*1000)
            if td > ttl:
                del self.tasks[task.id]

    def clear(self, task_id):
        task_run = self.__get_task(task_id)
        if task_run is TaskRun.RUNNING:
            raise TaskException('Task is running')
        self.__remove_task(task=task_run, force=True)

    @property
    def stats(self):
        result = {
            'total': len(self.tasks)
        }
        running = 0
        for id, run in self.tasks.items():
            result[id] = {
                'id': id,
                'status': run.status,
                'since': run.start_time
            }
            if run.status is TaskRun.RUNNING:
                running += 1
        result['running'] = running
        return result


class Task:
    def __init__(self, task_id=None, ttl=None):
        self.id = task_id or str(uuid4())
        self.ttl = ttl
        self.result = None
    
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
    def __init__(self, task_id, code, exec_type, ttl=None, data=None):
        super(CodeTask, self).__init__(task_id, ttl)
        self.code = code
        self.type = exec_type
        self.data = data
        
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
    
    def __init__(self, task_id, bytecode, fn_args, fn_kwargs, data, ttl=None):
        super(FunctionBytecodeTask, self).__init__(task_id, code=bytecode, data=data, exec_type="FunctionBytecode", ttl=ttl)
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

    def __LocalProcessBuilder(id, data):

        executable = data['executable']
        args = data['args']
        cwd = data.get('directory')

        process = LocalProcess(id=id, name=executable, args=args, cwd=cwd)

        return process

    def __SSHProcessBuilder(id, data):
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

    def __init__(self, process_type, process_data, task_id=None, ttl=None,
                 consume_process_out=False, buffer_size=100000):
        super(LocalProcessTask, self).__init__(task_id=task_id, ttl=ttl)
        self.process = None
        self.__build_process(process_type, process_data)
        self.buffer_size = buffer_size
        self.consume_process_out = consume_process_out

        if self.consume_process_out:
            self._setup_process_consumers()

    def _setup_process_consumers(self):
        self._out_buffer = deque(maxlen=self.buffer_size)
        self._err_buffer = deque(maxlen=self.buffer_size)
        self._out_consumer = Thread(target=self._consume_out, name='Consumer:OUT:%s' % self.id)
        self._err_consumer = Thread(target=self._consume_err, name='Consumer:ERR:%s' % self.id)

    def _consume_out(self):
        try:
            while self.process and self.process.output and not self.process.output.closed:
                line = self.process.output.readline()
                print('[OUT]%s' % line)
                if not line:
                    break
                self._out_buffer.appendleft(line)
        except:
            logging.exception('Failed to read process output')

    def _consume_err(self):
        try:
            while self.process and self.process.error and not self.process.error.closed:
                line = self.process.error.readline()
                print('[ERR]%s' % line)
                if not line:
                    break
                self._out_buffer.appendleft(line)
        except:
            logging.exception('Failed to read process error')

    def _run_consumers(self):
        if self.consume_process_out:
            self._out_consumer.start()
            self._err_consumer.start()

    def __build_process(self, process_type, process_data):
        builder = LocalProcessTask.PROCESS_BUILDERS.get(process_type)
        if not builder:
            raise ProcessTaskException('Unsupported process type %s' % process_type)
        try:
            self.process = builder(self.id, process_data)
        except Exception as e:
            raise ProcessTaskException('Failed to build process of type %s' % process_type) from e

    def run(self, context=None):
        print('Executing process %s' % self.process)
        self.process.execute()
        if self.consume_process_out:
            self._run_consumers()
        print('Process started. Waiting...')
        returncode = self.process.wait()
        print('Process ended with code %d' % returncode)
        try:
            if returncode:
                msg = self._handle_error(returncode)
            else:
                self.result = self._collect_result()
                print('[[RESULT]]: ', self.result)
        finally:
            self.process.close_streams()

    def _collect_result(self):
        result = ''
        print('Track process out -> ', self.consume_process_out)
        if self.consume_process_out:
            result += reduce(lambda a, b: a + str(b, 'utf-8'), self._out_buffer, '')
        return result

    def _handle_error(self, returncode):
        message = 'code: %d' % returncode
        if self.consume_process_out:
            err_msg = reduce(lambda a, b: a + str(b, 'utf-8'), self._err_buffer, '')
            message += err_msg

        raise ProcessTaskException(message)

    def stop(self, reason=None):
        self.process.kill()


def __local_process_task_from_message(msg):
    process_type = msg.headers.get('process-type')
    if not process_type:
        raise ProcessTaskException('No process type specified')
    process_data = msg.data['process']
    task_id = msg.headers.get('task-id') or str(uuid4())
    ttl = int(msg.headers.get('ttl') or 0)
    buffer_size = msg.headers.get('buffer-size')
    consume_out = msg.headers.get('consume-out') or False
    return LocalProcessTask(process_type=process_type, process_data=process_data, task_id=task_id,
                            ttl=ttl, buffer_size=buffer_size, consume_process_out=consume_out)

__TASK_BUILDERS = {
    'process': __local_process_task_from_message
}


def build_task(msg):
    task_type = msg.headers.get('task-type')
    if not task_type:
        raise TaskException('Task type missing')
    builder = __TASK_BUILDERS.get(task_type)
    if not builder:
        raise TaskException('Cannot build task of type %s' % task_type)
    return  builder(msg)