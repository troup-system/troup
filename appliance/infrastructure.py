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
    
    def __init__(self, name):
        self.name = name
        self.status = 'CREATED'
        
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


class ListenerWrapper:
    def __init__(self, delegate):
        self.delegate = self.__get_callable__(delegate)
    
    def __get_callable__(self, delegate):
        if isinstance(delegate, types.FunctionType) or \
           isinstance(delegate, types.MethodType):
            return delegate
        else:
            if hasattr(delegate, 'on_data'):
                return getattr(delegate, 'on_data')
        raise ChannelError('Invalid listener. It is not a callable object and does not contain on_data method.')
    
    def on_data(self, data):
        self.delegate(data)

class InboundChannel(Channel):
    
    def __init__(self, name, to_url):
        super(InboundChannel, self).__init__(name)
        self.listeners = []
    
    def register_listener(self, callback):
        listener = self.__wrap_listener__(self, callback)
        self.listeners.append(listener)
    
    def __wrap_listener__(self, callback):
        return ListenerWrapper(callback)
    

class OutboundChannel(Channel):
    
    def __init__(self, name, to_url):
        super(OutboundChannel, self).__init__(name)
    
    def send(self, data):
        pass

class FullDuplexChannel(InboundChannel, OutboundChannel):
    
    def __init__(self, name, to_url):
        super(FullDuplexChannel, self).__init__(name, to_url)




