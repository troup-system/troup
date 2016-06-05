__author__ = 'pavle'

import sys

sys.path.append('..')

from troup.client import CommandAPI, client_to_local_node
import time

cmd = CommandAPI(channel_client=client_to_local_node())

promise = cmd.send(CommandAPI.task('LocalProcess', {
    'directory': '/home/pavle',
    'executable': '/usr/bin/ls',
    'args': ['-l', '-a']
}, track_out=True, ttl=10000))
print(promise)
print('cmd send')
try:
    result = promise.result
    print('Result -> %s' % str(result))
    time.sleep(2)
    def on_task_result(res):
        print('Task result %s' % res)

    task_result_cmd = CommandAPI.command('task-result', {'task-id': result})
    promise = cmd.send(task_result_cmd, on_reply=on_task_result)
    print('Task result request send')
    ls_res = promise.result
    print('Result: %s' % ls_res)
finally:
    cmd.shutdown()
    print('done')
