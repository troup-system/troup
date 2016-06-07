import unittest
import sys

sys.path.append('..')

import time
from troup.tasks import Task, TaskRun, TasksRunner


class DemoTask(Task):

    def run(self, context=None):
        print('[%s] Task run' % self.id)

    def stop(self, reason=None):
        print('[%s] Task stop - reason %s' %(self.id, reason))


class TaskRunTest(unittest.TestCase):

    def test_create_task(self):
        task = DemoTask()
        run = TaskRun(task=task)
        assert run.status is TaskRun.CREATED

    def test_create_task(self):
        task = DemoTask()
        run = TaskRun(task=task)
        assert run.status is TaskRun.CREATED
        run.start()
        if run.status is TaskRun.ERROR:
            raise Exception() from run.error
        assert run.status is TaskRun.DONE


class DelayedTestTask(Task):

    def __init__(self, delay=1):
        super(DelayedTestTask, self).__init__()
        self.delay = delay

    def run(self, context=None):
        print('[%s] task sleeping for %f seconds' % (self.id, self.delay))
        time.sleep(self.delay)
        print('[%s] task done' % self.id)

    def stop(self, reason=None):
        print('[%s] done' % self.id)


class TasksRunnerTest(unittest.TestCase):

    def setUp(self):
        self.runner = TasksRunner()

    def tearDown(self):
        self.runner.shutdown()

    def test_start_task(self):
        task = DemoTask(task_id='task-demo-0')
        run = self.runner.run(task)
        assert run

    def test_stop_task(self):
        dt = DelayedTestTask()
        run = self.runner.run(dt)
        assert run
        time.sleep(0.5)
        assert run.status is TaskRun.RUNNING
        self.runner.stop(dt.id, wait=True)
        assert run.status is TaskRun.DONE

if __name__ == '__main__':
    unittest.main()