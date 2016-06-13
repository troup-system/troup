import sys

sys.path.append('..')

from troup.client import CommandAPI, client_to_local_node, ChannelClient

#cc = ChannelClient(nodes_specs=['RPI:ws://192.168.2.128:7000'])
cc = client_to_local_node()

cmd = CommandAPI(channel_client=cc)

promise = cmd.send(CommandAPI.command('apps', {}))
print(promise)
print('cmd send')
try:
    result = promise.result
    print('Result -> %s' % str(result))
finally:
    cmd.shutdown()
    print('done')
