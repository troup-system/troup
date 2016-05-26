import sys

sys.path.append('..')

from troup.client import CommandAPI, client_to_local_node

cmd = CommandAPI(channel_client=client_to_local_node())

promise = cmd.send_command(cmd.command('info', {}))
print(promise)
print('cmd send')
try:
    result = promise.result
    print('Result -> %s' % str(result))
finally:
    cmd.shutdown()
    print('done')
