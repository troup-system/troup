__author__ = 'pavle'

from troup.store import InMemorySyncedStore
from troup.infrastructure import AsyncIOWebSocketServer, IncomingChannelWSAdapter, ChannelManager, message_bus, bus
from troup.system import StatsTracker
from troup.messaging import message, serialize, deserialize, deserialize_dict, Message
import threading
from troup.threading import IntervalTimer
from troup.apps import App
from troup.process import this_process_info_file, open_process_lock_file, open_process_lock_file
import random
from math import ceil
from os import getpid
import logging


class Node:

    def __init__(self, node_id, config):
        self.node_id = node_id
        self.config = config
        self.store = self._build_store_()
        self.channel_manager = None
        self.aio_server = None
        self.stats_tracker = None
        self.sync_manager = None
        self.bus = message_bus
        self.lock = None
        self.pid = getpid()
        self.commands = {}

    def __lock(self):
        if self.lock:
            return self.lock
        self.__check_lock()
        self.lock = local_node_lock_file({"name": self.node_id})
        return self.lock

    def __check_lock(self):
        lock = check_local_node_lock()
        if lock and lock.pid != self.pid:
            raise Exception('Seems there is a node already running. PID is %d. ' +
                            'If no node with this pid is running, then you may ' +
                            'have to delete the file manually.' % lock.pid)

    def _start_channel_manager_(self):
        aio_srv = AsyncIOWebSocketServer(host=self.config['server'].get('hostname'), port=self.config['server']['port'], web_socket_class=IncomingChannelWSAdapter)
        def start_aio_server():
            print('AIO Server start')
            aio_srv.start()
            print('AIO Server end')
        th = threading.Thread(target=start_aio_server)
        th.start()
        print('Notify aio server to start')
        channel_manager = ChannelManager(aio_srv)
        self.aio_server = aio_srv
        return channel_manager

    def __register_message_dispatcher__(self):
        def on_channel_data(message_str, channel):
            try:
                msg = deserialize(message_str)
                if msg.headers.get('type'):
                    self.bus.publish(msg.headers['type'], msg, channel)
                else:
                    self.bus.publish('__message.genericType', msg, channel)
            except Exception as e:
                self.log.exception('Failed to handle channel data', e)
        self.channel_manager.on('channel.data', on_channel_data)

    def _build_store_(self):
        store = InMemorySyncedStore(root_path=self.config['store']['path'])
        return store

    def _start_stats_tracker_(self):
        self.stats_tracker = StatsTracker(period=self.config['stats']['update_interval'])
        print('stats tracking ON')

    def _start_sync_manager_(self):
        self.sync_manager = SyncManager(node=self, channel_manager=self.channel_manager, event_processor=None, sync_interval=10000, sync_percent=0.3)
        self.sync_manager.start()

        neighbours = self.config.get('neighbours')
        if neighbours:
            for url in neighbours:
                name, sep, endpoint = url.partition(':')
                node = NodeInfo(name=name, stats=None, apps=None, endpoint=endpoint)
                self.sync_manager.register_node(node)
                print('Added neighbour %s [%s]' % (name, endpoint))

    def __register_to_local(self):
        if self.config.get('lock'):
            endpoint = self.aio_server.get_server_endpoint()
            self.lock.set_info('url', endpoint)

    def __register_command_handlers(self):
        @bus.subscribe('task')
        def __on_task__(task, inc_channel):
            print('Received task: %s' % task)

        @bus.subscribe('command')
        def __on_command__(command, inc_channel):
            print('Received command: %s over channel %s' % (command, inc_channel))
            self.__process_command(command, inc_channel)

    def __register_commands(self):
        pass

    def __process_command(self, command, channel):
        handler = self.commands.get(command.headers['command'])
        if not handler:
            self.__reply_to_command(command, reply='Unknown command', error=True, channel=channel)
            return
        try:
            reply = handler(command)
            self.__reply_to_command(command, reply=reply, channel=channel)
        except Exception as e:
            self.__reply_to_command(command, reply=e.message, error=True, channel=channel)
            logging.exception('Failed to execute command %s', command)

    def __reply_to_command(self, command, reply, channel, error=None):
        reply_msg = message().header('reply-for-command', command.id).\
            header('type', 'command-reply').\
            value('error', error).value('reply', reply).build()
        ser_msg = serialize(reply_msg)
        channel.send(ser_msg)
        print('Replied -> %s' % ser_msg)

    def get_available_apps(self):
        return [app.name for app in self.store.apps]

    def get_stats(self):
        pass

    def get_apps(self):
        pass

    def query(self, q):
        pass

    def run_app(self, app_name):
        pass

    def start(self):
        if self.config.get('lock'):
            self.__lock()
        self.channel_manager = self._start_channel_manager_()
        print('Node %s started' % self.node_id)
        self._start_stats_tracker_()
        self._start_sync_manager_()
        self.__register_message_dispatcher__()
        self.__register_to_local()
        self.__register_command_handlers()

    def stop(self):
        print('node stop')
        if self.stats_tracker:
            self.stats_tracker.stop_tracking()
            print('Statistics tracking has stopped')
        if self.aio_server:
            self.aio_server.stop()
            print('Async I/O Server notified to stop')
        if self.sync_manager:
            self.sync_manager.stop()
        if self.lock:
            self.lock.unlock()

    def get_node_info(self):
        return NodeInfo(name=self.node_id, stats=self.stats_tracker.get_stats(), apps=self.get_apps(), endpoint=self.aio_server.get_server_endpoint())


class NodeInfo:
    def __init__(self, name=None, stats=None, apps=None, endpoint=None):
        self.name = name
        self.stats = stats
        self.apps = apps
        self.endpoint = endpoint


def node_info_from_dict(node_dict):
    apps = []
    dapps = node_dict.get('apps') or []

    for dapp in dapps:
        app = deserialize_dict(dapp, App)
        apps.append(app)
    node = deserialize_dict(node_dict, NodeInfo)
    node.apps = apps
    return node


class RandomBuffer:

    def __init__(self, nodes_dict):
        self.nodes_dict = nodes_dict
        self.buffer = []
        self._shuffle_()

    def next(self, n):
        n = int(ceil(n))
        while len(self.buffer) < n:
            self._shuffle_()
        shuffled = self.buffer[0:n]
        self.buffer = self.buffer[n:]
        return shuffled

    def _shuffle_(self):
        nodes = [name for name, node in self.nodes_dict.items()]
        random.shuffle(nodes)
        self.buffer = self.buffer + nodes


class SyncManager:

    def __init__(self, node, channel_manager, event_processor, sync_interval=60000, sync_percent=0.3):
        self.node = node
        self.channel_manager = channel_manager
        self.event_processor= event_processor
        self.sync_percent = sync_percent
        self.known_nodes = {}
        self.random_buffer = RandomBuffer(self.known_nodes)
        self.sync_timer = IntervalTimer(offset=sync_interval, interval=sync_interval, target=self.sync_random_nodes)

    def _on_message_(self, msg_str, channel):
        msg = deserialize(msg_str, as_type=Message)
        #print('Got message [%s]' % msg.__dict__)
        if msg.headers.get('type') == 'sync-message':
            self._on_sync_message_(msg)

    def _on_sync_message_(self, msg):
        #print('Got sync message -> %s' % msg)
        #print(' : From node %s(%s)' % (msg.data['node']['name'], msg.data['node']['endpoint']))
        nodes = [node_info_from_dict(msg.data['node'])]

        known_nodes = [node_info_from_dict(node) for node in msg.data['known_nodes']]
        nodes = nodes + known_nodes
        self._merge_nodes_list_(nodes)

    def _merge_nodes_list_(self, nodes):
        for node in nodes:
            if node.name == self.node.node_id:
                continue
            if not self.known_nodes.get(node.name):
                self.known_nodes[node.name] = node
                print('Node %s has joined' % node.name)
                self._print_known_nodes_()
            self._merge_node_(node)

    def _print_known_nodes_(self):
        print(' Members: ')
        for name, node in self.known_nodes.items():
            print('   %s[%s]' % (name, node.endpoint))

    def _merge_node_(self, node):
        existing = self.known_nodes[node.name]
        self.known_nodes[node.name] = node
        if existing.endpoint != node.endpoint:
            self.channel_manager.close_channel(existing.endpoint)

    def _on_closed_channel_(self, channel):
        to_remove = []
        for name, node in self.known_nodes.items():
            if node.endpoint == channel.to_url:
                to_remove.append(name)

        for name in to_remove:
            del self.known_nodes[name]

    def start(self):
        self.sync_timer.start()

        self.channel_manager.on('channel.closed', self._on_closed_channel_)
        self.channel_manager.on('channel.data', self._on_message_)

    def stop(self):
        self.sync_timer.cancel()
        self.channel_manager.remove_listener('channel.closed', self._on_closed_channel_)

    def register_node(self, node):
        if self.known_nodes.get(node.name):
            self._merge_node_(node)
        else:
            self.known_nodes[node.name] = node

    def unregister_node(self, node):
        pass

    def sync_random_nodes(self):
        nodes = self.random_buffer.next(len(self.known_nodes) * self.sync_percent)

        for name in nodes:
            if self.known_nodes.get(name):
                node = self.known_nodes[name]
                print('Sync with %s [%s]' % (name, node.endpoint))
                self.channel_manager.send(to_url=node.endpoint, data=serialize(self.get_sync_message(), indent=2))

    def sync_one_node(self, node, this_node_info):
        pass

    def get_sync_message(self):
        return message().value('node', self.node.get_node_info()).\
            value('known_nodes', [n for k,n in self.known_nodes.items()]).\
            value('type', 'sync-message').build()



NODE_LOCK_FILE_PATH = '/tmp/troup.node.lock'


def local_node_lock_file(node_info=None):
    return this_process_info_file(NODE_LOCK_FILE_PATH, info=node_info, create=True)

def check_local_node_lock():
    return open_process_lock_file(NODE_LOCK_FILE_PATH)

def read_local_node_lock():
    return open_process_lock_file(NODE_LOCK_FILE_PATH, read_only=True)
