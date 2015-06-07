import logging

__author__ = 'pavle'

from types import FunctionType
from types import MethodType


class ChannelError(Exception):
    pass


class Channel:
    
    CREATED = 'CREATED'
    CONNECTING = 'CONNECTING'
    OPEN = 'OPEN'
    CLOSING = 'CLOSING'
    CLOSED = 'CLOSED'
    ERROR = 'ERROR'
    
    def __init__(self, name, to_url):
        self.name = name
        self.status = 'CREATED'
        self.listeners = []
        
    def open(self):
        if self.status is not Channel.CREATED:
            raise ChannelError('Unable to open channel')
        try:
            self.status = Channel.CONNECTING
            self.connect()
            self.status = Channel.OPEN
        except Exception as e:
            self.status = Channel.ERROR
            raise ChannelError(e)
        
    def close(self):
        if self.status is not Channel.OPEN:
            raise ChannelError('Unable to close channel')
        try:
            self.status = Channel.CLOSING
            self.disconnect()
            self.status = Channel.CLOSED
        except Exception as e:
            self.status = Channel.ERROR
            raise ChannelError(e)
    
    def connect(self):
        pass
        
    def disconnect(self):
        pass
    
    def register_listener(self, callback):
        listener = self.__wrap_listener__(self, callback)
        self.listeners.append(listener)
    
    def __wrap_listener__(self, callback):
        return ListenerWrapper(callback)
    
    def send(self, data):
        pass

    def data_received(self, data):
        for listener in self.listeners:
            try:
                listener.on_data(data)
            except Exception as e:
                logging.warning('Listener error: ', e)


class ListenerWrapper:
    def __init__(self, delegate):
        self.delegate = self.__get_callable__(delegate)
    
    def __get_callable__(self, delegate):
        if isinstance(delegate, FunctionType) or \
           isinstance(delegate, MethodType):
            return delegate
        else:
            if hasattr(delegate, 'on_data'):
                return getattr(delegate, 'on_data')
        raise ChannelError('Invalid listener. It is not a callable object and does not contain on_data method.')
    
    def on_data(self, data):
        self.delegate(data)


#from ws4py.websocket import WebSocket
from ws4py.async_websocket import WebSocket
from threading import Event


class IncommingChannel(Channel):
    
    def __init__(self, name, to_url, adapter=None):
        super(IncommingChannel, self).__init__(name, to_url)
        self.adapter = adapter
        self.close_event = Event()
    
    def disconnect(self):
        self.adapter.close(code=1000, reason="client-closing")
        # TODO: Wait to actually close
        self.close_event.wait()
    
    def notify_close(self):
        self.close_event.set()
    
    def send(self, data):
        if self.status is Channel.OPEN:
            self.adapter.send(payload=data)
        else:
            raise ChannelError('Not open')


class IncomingChannelWSAdapter(WebSocket):
    
#    def __init__(self, sock, protocols=None, extensions=None, \
#        environ=None, heartbeat_freq=None)
#        super(IncomingChannelWSAdapter, self).__init__(sock=sock, protocols=protocols,\
#        extensions=extensions, environ=environ, heartbeat_freq=heartbeat_freq)
    def __init__(self, protocol):
        print('Adapter starts... Protcol: %s' % str(protocol) )
        #super(IncomingChannelWSAdapter, self).__init__(protocol)
        WebSocket.__init__(self, protocol)
        self.server = None 
        
        self.channel = None
        print('Adapter started')
    
    def opened(self):
        self.server = self.proto.server
        try:
            self.channel = IncommingChannel(
                name="channel[%s-%s]" % (self.local_address, self.peer_address),
                to_url=str(self.peer_address),
                adapter=self)
            self.channel.open()
            self.server.on_channel_open(self.channel)
        except Exception as e:
            logging.exception(e)
            raise e
    
    def closed(self, code, reason=None):
        print('closing ws. code=%s, reason=%s'%(str(code),str(reason)))
        self.channel.notify_close()
        self.server.on_channel_closed(self.channel)
    
    def received_message(self, message):
        print(' -> %s' % str(message))
        try:
            self.channel.data_received(message.data)
        except Exception as e:
            logging.exception(e)

    @property
    def local_address(self):
        """
        Local endpoint address as a tuple
        """
        if not self._local_address:
            self._local_address = self.proto.reader._transport.get_extra_info('sockname')
            if len(self._local_address) == 4:
                self._local_address = self._local_address[:2]
        return self._local_address

    @property
    def peer_address(self):
        """
        Peer endpoint address as a tuple
        """
        if not self._peer_address:
            self._peer_address = self.proto.reader._transport.get_extra_info('peername')
            if len(self._peer_address) == 4:
                self._peer_address = self._peer_address[:2]
        return self._peer_address
    

from ws4py.server.tulipserver import WebSocketProtocol


class ServerAwareWebSocketProtocol (WebSocketProtocol):

    def __init__(self, handler_class, server):
        super(ServerAwareWebSocketProtocol, self).__init__(handler_class)
        self.server = server


import asyncio


class AsyncIOWebSocketServer:
    
    def __init__(self, host='', port=1700, web_socket_class=IncomingChannelWSAdapter):
        self.host = host
        self.port = port
        self.web_socket_class = web_socket_class
        self.aio_loop = asyncio.get_event_loop()
        self.running = False
        self.channels = {}
        
    def start(self):
        proto = lambda: ServerAwareWebSocketProtocol(self.web_socket_class, self)
        sf = self.aio_loop.create_server(proto, self.host, self.port)
        s = self.aio_loop.run_until_complete(sf)
        print('stared on %s' % str(s.sockets[0].getsockname()))
        self.aio_loop.run_forever()
        
    def stop(self):
        self.aio_loop.stop()
        
    def on_channel_open(self, channel):
        self.channels[channel.name] = channel
        print('Channel %s => %s added' % (channel.name, channel))
    
    def on_channel_closed(self, channel):
        del self.channels[channel]
    
    


