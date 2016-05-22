from troup.infrastructure import OutgoingChannelOverWS
from troup.distributed import Promise
from troup.threading import IntervalTimer
from troup.node import read_local_node_lock
from troup.messaging import message, serialize, deserialize


from datetime import datetime, timedelta

class CallbackWrapper:
    def __init__(self, callback, valid_for, promise=None, created_on=None):
        self.callback = callback
        self.valid_for = valid_for
        self.created_on = created_on or datetime.now()
        self.promise = promise or Promise()

    def check_expired(self):
        if datetime.now() > (timedelta(milliseconds=self.valid_for) + self.created_on):
            self.promise.complete(error='Timeout', result=Exception('Timeout'))
    def execute_callback(self, result):
        if self.callback:
            try:
                self.callback(result)
            except Exception as e:
                print('Woops')
        self.promise.complete(result=result)

class ChannelClient:

    def __init__(self, nodes_specs=None, reply_timeout=5000, check_interval=5000):
        self.nodes_ref = {}
        self.channels = {}
        self.callbacks = []
        self.reply_timeout = reply_timeout
        self.check_interval = check_interval
        self.maintenance_timer = self.__build_timer()
        self.__build_nodes_refs__(nodes_specs)

    def __build_nodes_refs__(self, nodes_specs):
        for spec in nodes_specs:
            parsed = spec.partition(':')
            self.nodes_ref[parsed[0]] = parsed[2]

    def __build_timer(self):
        timer = IntervalTimer(interval=self.check_interval, offset=self.check_interval, target=self.__check_expired_callbacks)
        timer.start()
        return timer

    def __check_expired_callbacks(self):
        for wrapper in self.callbacks:
            wrapper.check_expired()

    def send_message(self, message, to_node=None, on_reply=None):
        def reply_callback_wrapper(*args, **kwargs):
            if on_reply:
                on_reply(*args, **kwargs)

        ser_message = serialize(message)

        if to_node:
            self.send_message_to_node(ser_message, to_node, reply_callback_wrapper)
        else:
            for name, node in self.nodes_ref.items():
                self.send_message_to_node(ser_message, name, reply_callback_wrapper)

    def send_message_to_node(self, message, node, on_reply):
        channel = self.get_channel(node)
        channel.send(message)


    def get_channel(self, for_node):
        channel = self.channels.get(for_node)
        if not channel:
            channel = self.build_channel(for_node)
        return channel

    def build_channel(self, for_node):
        ref = self.nodes_ref.get(for_node)
        if not ref:
            raise Exception('Unknown node reference [%s]' % for_node)
        return self.create_channel(for_node, ref)

    def create_channel(self, node_name, reference):
        def opened(*args):
            print('OPENED')

        chn =  OutgoingChannelOverWS(node_name, reference)
        chn.on('open', opened)
        chn.open()
        import time
        time.sleep(2)
        return chn


def client_to_local_node():

    lock = read_local_node_lock()
    client = ChannelClient(nodes_specs=['%s:%s'%(lock.get_info('name'), lock.get_info('url'))])
    return client


class CommandAPI:

    def __init__(self, channel_client):
        self.channel_client = channel_client

    def send_command(self, command, to_node=None, on_reply=None):
        return self.channel_client.send_message(message=command, to_node=to_node, on_reply=on_reply)

    def monitor(self, command_ref):
        pass

    def command(self, name, data):
        return message(data=data).header('type', 'command').build()
