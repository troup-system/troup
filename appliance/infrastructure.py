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
        self.event_listeners = {}
        
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
    
    def on(self, event_name, callback):
        callbacks = self.event_listeners.get(event_name)
        if not callbacks:
            callbacks = self.event_listeners[event_name] = []
        if not callback in callbacks:
            callbacks.append(callback)
    
    def trigger(self, event, *data):
        callbacks = self.event_listeners.get(event_name)
        if callbacks:
            for callback in callbacks:
                try:
                    callback(*data)
                except Exception as e:
                    logging.debug('An error while triggering event {}', event, e)

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
        self.listeners = []
        
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
    
    def on_event(self, callback):
        self.listeners.append(callback)
    
    def notify_event(self, event, channel):
        for listener in listeners:
            listener(event, channel)
    
# -- outgoing connection

from ws4py.client.threadedclient import WebSocketClient


class OutgoingChannelWSAdapter(WebSocketClient):
    
    def __init__(self, url, handlers):
        super(OutgoingChannelWSAdapter, self).__init__(url=url)
        self.handlers = handlers
    
    def __noop__(self, *args, **kwargs):
        pass
    
    def __handler__(self, name):
        return self.handlers.get(name) or self.__noop__
    
    def opened(self):
        self.__handler__('opened')()
    
    def closed(self, code, reason=None):
        self.__handler__('closed')(code, reason)
    
    def received_message(self, m):
        if m and m.data:
            self.__handler__('on_data')(m.data)


class OutgoingChannelOverWS(Channel):
    
    def __init__(self, name, to_url):
        super(OutgoingChannelOverWS, self).__init__(name, to_url)
        self.web_socket = OutgoingChannelWSAdapter(url=to_url,
           handlers={
                'opened': self._on_open_handler_,
                'closed': self._on_closed_handler_,
                'on_data': self.data_received
           })
    
    def _on_open_handler_(self):
        self.trigger('open', self)
        self.on_opened()
    
    def on_opened(self):
        pass
    
    def _on_closed_handler_(self, code, reason=None):
        self.trigger('closed', self, code, reason)
        self.on_closed(code, reason)
    
    def on_closed(self, code, reason=None):
        pass
    
    def connect(self):
        self.web_socket.connect()
    
    def disconnect(self):
        self.web_socket.close()


class ChannelManager:
    
    def __init__(self, config, aio_server):
        self.config = config
        self.aio_server = aio_server
        self.channels = {}
        self.log = logging.get_logger('channel-manager')
        
    def channel(self, name=None, to_url=None):
        if self.channels.get(name):
            return self.channels[name]
        if not to_url:
            raise Exception('No channel URL specified')
        channel = self.open_channel_to(name, to_url)
        self.channels[name] = channel
        return channel
    
    def open_channel_to(self, url):
        och = OutgoingChannelOverWS(name=name, to_url=url)
        och.on('closed', self._handle_closed_channel_)
        return och
    
    def _handle_closed_channel_(self, channel, code, reason=None):
        del self.channels[channel.name]
    
    def listen(self, name=None, to_url=None, listener=None):
        pass
    
    def send(self, name=None, to_url=None, data=None):
        pass
    



# -- simlest message bus in the world

class MessageBus:
    
    def __init__(self):
        self.subscribers = {}
    
    def on(self, topic, handler):
        if not handler:
            raise Exception('Handler not specified')
        if not topic:
            raise Exception('Topic not specified')
        subscribers = self.__get_subscribers__(topic)
        if handler in subscribers:
            raise Exception('Handler already registered')
        subscribers.append(handler)
    
    def __get_subscribers__(self, topic):
        subscribers = self.subscribers.get(topic)
        if not subscribers:
            subscribers = []
            self.subscribers[topic] = subscribers
        return subscribers
    
    def publish(self, topic, event):
        subscribers = self.subscribers.get(topic)
        if subscribers:
            for handler in subscribers:
                try:
                    handler(event)
                except Exception as e:
                    print('Woops')
    
    
    def remove(self, topic, handler):
        subscribers = self.subscribers.get(topic)
        if subscribers:
            subscribers.remove(handler)
    
    




