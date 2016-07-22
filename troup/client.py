# Copyright 2016 Pavle Jonoski
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from troup.infrastructure import OutgoingChannelOverWS
from troup.distributed import Promise
from troup.threading import IntervalTimer
from troup.node import read_local_node_lock
from troup.messaging import message, serialize, deserialize, Message

from threading import Thread
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
        self.callbacks = {}
        self.reply_timeout = reply_timeout
        self.check_interval = check_interval
        self.maintenance_timer = self.__build_timer()
        self.__build_nodes_refs__(nodes_specs)

    def __build_nodes_refs__(self, nodes_specs):
        for spec in nodes_specs:
            parsed = spec.partition(':')
            self.nodes_ref[parsed[0]] = parsed[2]

    def __build_timer(self):
        timer = IntervalTimer(interval=self.check_interval, offset=self.check_interval,
                              target=self.__check_expired_callbacks)
        timer.start()
        return timer

    def __check_expired_callbacks(self):
        for msgid, wrapper in self.callbacks.items():
            wrapper.check_expired()

    def __reg_wrapper(self, message, callback):
        wrapper = CallbackWrapper(callback=callback, valid_for=5000)
        self.callbacks[message.id] = wrapper
        return wrapper

    def __on_channel_data(self, data, channel):
        msg = deserialize(data, Message)
        if msg.headers.get('type') == 'reply':
            self.__process_reply(msg)

    def __process_reply(self, reply):
        id = reply.headers.get('reply-for')
        if not id:
            raise Exception('Invalid reply %s' % reply)
        wrapper = self.callbacks.get(id)
        if wrapper:
            if reply.data.get('error'):
                wrapper.promise.complete(error=reply.data.get('reply'))
            else:
                wrapper.promise.complete(result=reply.data.get('reply'))

    def send_message(self, message, to_node=None, on_reply=None):
        def reply_callback_wrapper(*args, **kwargs):
            if on_reply:
                on_reply(*args, **kwargs)
        wrapper_promise = Promise()
        def do_send():
            promises = []
            if to_node:
                promise = self.send_message_to_node(message, to_node, reply_callback_wrapper)
                promises.append(promise)
            else:
                for name, node in self.nodes_ref.items():
                    promise = self.send_message_to_node(message, name, reply_callback_wrapper)
                    promises.append(promise)
            results = []
            for p in promises:
                results.append(p.result)
            if len(results) == 1:
                wrapper_promise.complete(result=results[0])
            else:
                wrapper_promise.complete(result=True)

        def run_in_thread():
            try:
                do_send()
            except Exception as e:
                wrapper_promise.complete(error=e)

        Thread(target=run_in_thread).start()
        return wrapper_promise

    def send_message_to_node(self, message, node, on_reply):
        channel = self.get_channel(node)
        wrapper = self.__reg_wrapper(message=message, callback=on_reply)
        ser_message = serialize(message)
        channel.send(ser_message)
        return wrapper.promise

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
        chn = OutgoingChannelOverWS(node_name, reference)

        def on_data(data):
            #print('DATA %s' % data)
            self.__on_channel_data(data, channel=chn)

        chn.register_listener(on_data)
        chn.open()
        self.channels[node_name] = chn
        return chn

    def shutdown(self):
        for name, channel in self.channels.items():
            channel.close()
        self.maintenance_timer.cancel()


def client_to_local_node():
    lock = read_local_node_lock()
    client = ChannelClient(nodes_specs=['%s:%s' % (lock.get_info('name'), lock.get_info('url'))])
    return client


class CommandAPI:
    def __init__(self, channel_client):
        self.channel_client = channel_client

    def send(self, command, to_node=None, on_reply=None):
        return self.channel_client.send_message(message=command, to_node=to_node, on_reply=on_reply)

    def monitor(self, command_ref):
        pass

    def command(name, data):
        return message(data=data).header('type', 'command').header('command', name).build()

    def task(type, data, ttl=None, track_out=False, buffer=None):
        return message().header('type', 'task').header('ttl', ttl).\
            header('task-type', 'process').header('process-type', type).\
            header('consume-out', track_out).header('buffer-size', buffer).\
            value('process', data).build()

    def shutdown(self):
        self.channel_client.shutdown()


if __name__ == '__main__':
    from argparse import ArgumentParser
    from json import loads, dumps

    parser = ArgumentParser(prog="troup.client", description="Low level troup system client")

    parser.add_argument('--node', help='Node connection URL.', default='ws://localhost:7000')
    parser.add_argument('-t', '--type', default='command', help='Message type. May be "command" or "task".')
    parser.add_argument('-d', '--data', help='Message data. This is usually a JSON string.')
    parser.add_argument('-H', '--header', nargs='+', help='Message headers in the form HEADER_NAME=VALUE.')

    parser.add_argument('--reply-timeout', default=5000, help='Message reply timeout in milliseconds.')
    parser.add_argument('--check-interval', default=1000, help='Interval to check for timeouts in milliseconds.')

    parser.add_argument('-c', '--command', help='The command name. Used only when type is "command".')

    parser.add_argument('-v', '--verbose', help='Be more verbose.', action='store_true')

    parser.add_argument('--as-json', action='store_true',
                        help='Try to serialize the result as JSON and print it on stdout.')

    args = parser.parse_args()

    def printout(*arguments):
        if args.verbose:
            print(*arguments)

    data = args.data or '{}'
    data = loads(data)

    mb = message(data=data)
    for header in args.header or []:
        try:
            header_name, value = header.split('=')
            mb.header(header, value)
        except Exception as e:
            raise Exception('Invalid header value %s' % header) from e

    mb.header('type', args.type)

    if args.type == 'command' and args.command:
        mb.header('command', args.command)

    try:
        message = mb.build()

        channel_client = ChannelClient(nodes_specs=['TARGET:%s'%args.node], reply_timeout=args.reply_timeout,
                                       check_interval=args.check_interval)

        api = CommandAPI(channel_client=channel_client)

        printout('Sending to ', args.node)

        promise = api.send(command=message, to_node='TARGET')

        result = promise.result

        if args.as_json:
            print(dumps(result))
        else:
            print(result)
    finally:
        if api:
            api.shutdown()