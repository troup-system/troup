import sys

sys.path.append('..')

from troup.client import CommandAPI, client_to_local_node

cmd = CommandAPI(channel_client=client_to_local_node())

cmd.send_command(cmd.command('test', {}))
print('cmd send')
cmd.shutdown()
print('done')
