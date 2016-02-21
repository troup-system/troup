import asyncio

import threading

class TestProtocol(asyncio.Protocol):
    
    def connection_made(self, transport):
        print('connection_made')
    
    def data_received(self, data):
        print('data_received')
    
    def connection_lost(self, exc):
        print('connection_lost')    
     

loop = asyncio.get_event_loop()
server = loop.run_until_complete(loop.create_server(TestProtocol, 'localhost', 15001))

def run_server():
    print('run_forever...')
    loop.run_forever()
    print('server exit')
    loop.close()
    print('loop closed')

#@asyncio.coroutine
def stop_loop(loop):
    print('loop stop')
    loop.stop()
    print('loop indeed stop')
    

srv_thread = threading.Thread(target=run_server)

srv_thread.start()

import time

time.sleep(1)

def stop_server():
    server.close()
    print('server close')
    loop.call_soon_threadsafe(stop_loop, loop) # must schedule with threadsafe


stop_server()

print('all out')
