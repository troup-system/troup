import sys

sys.path.append('..')

print(sys.path)

from troup.infrastructure import AsyncIOWebSocketServer, IncomingChannelWSAdapter
from ws4py.async_websocket import EchoWebSocket

server = AsyncIOWebSocketServer(host='', port=8910, web_socket_class=IncomingChannelWSAdapter)

def run_server():
    print('Srv run')
    server.start()
    print('Srv end')

import threading

t = threading.Thread(target=run_server)

t.start()
