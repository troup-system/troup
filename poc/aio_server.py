import sys

sys.path.append('..')

print(sys.path)

from appliance.infrastructure import AsyncIOWebSocketServer, IncomingChannelWSAdapter
from ws4py.async_websocket import EchoWebSocket

server = AsyncIOWebSocketServer(host='', port=8910, web_socket_class=IncomingChannelWSAdapter)

def start_server():
    server.start()

import threading

t = threading.Thread(target=start_server)
t.start()

t.join()
