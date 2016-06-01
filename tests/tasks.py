import unittest
import sys

sys.path.append('/..')


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


class TasksRunnerTest(unittest.TestCase):

    def setUp(self):
        self.runner = TasksRunner()

    def tearDown(self):
        self.runner.shutdown()

    def test_start_task(self):
        task = DemoTask(task_id='task-demo-0')
        future = self.runner.run(task)
        assert future

    def test_stop_task(self):
        pass

if __name__ == '__main__':
    unittest.main()