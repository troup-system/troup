__author__ = 'pavle'


import sys

sys.path.append('..')

from troup.client import CommandAPI, client_to_local_node

cmd = CommandAPI(channel_client=client_to_local_node())

promise = cmd.send(CommandAPI.task('LocalProcess', {
    'directory': '/home/pavle/projects',
    'executable': '/usr/bin/xterm',
    'args': []
}, track_out=True))
print(promise)
print('cmd send')
try:
    result = promise.result
    print('Result -> %s' % str(result))
finally:
    cmd.shutdown()
    print('done')
