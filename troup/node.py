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

__author__ = 'pavle'

from troup.store import InMemorySyncedStore
from troup.infrastructure import AsyncIOWebSocketServer, IncomingChannelWSAdapter, ChannelManager, ChannelClosedError, message_bus, bus
from troup.system import StatsTracker, SystemStats
from troup.messaging import message, serialize, deserialize, deserialize_dict, Message
import threading
from troup.threading import IntervalTimer
from troup.apps import App
from troup.process import this_process_info_file, open_process_lock_file
from troup.tasks import TasksRunner, build_task, task_for_app
import random
from math import ceil
from os import getpid
from functools import reduce
import logging


class Node:
    """Basic interface for interaction with the system and the basic unit of the
    system.
    
    A Node tracks system stats, interacts with other nodes and ultimatly manages
    the execution of tasks and commands.
    
    The system is comprised of multiple nodes coordinating between themselves.
    Usually there is one node per machine.
    
    * *node_id* is the node identifier. This should be uniqe on the system.
    * *config* is the configuration :func:`dict` for the node.
    * *store* is the :class:`troup.store.Store` instance used by this node.
    """
    def __init__(self, node_id, config, store=None, channel_manager=None,
                 aio_server=None, stats_tracker=None, sync_manager=None,
                 tasks_runner=None):
        self.node_id = node_id

        self.log = logging.getLogger('Node(%s)' % self.node_id)

        self.config = config
        self.store = store or self._build_store_()
        self.channel_manager = channel_manager or None
        self.aio_server = aio_server or None
        self.stats_tracker = stats_tracker or None
        self.sync_manager = sync_manager or None
        self.bus = message_bus
        self.lock = None
        self.pid = getpid()
        self.commands = {}
        self.runner = tasks_runner or TasksRunner(max_workers=int(self.config.get('runner-max-workers', '3')))

        self.__register_commands()

    def __lock(self):
        if self.lock:
            return self.lock
        self.__check_lock()
        self.lock = local_node_lock_file({"name": self.node_id})
        return self.lock

    def __check_lock(self):
        lock = check_local_node_lock()
        if lock and lock.pid != self.pid:
            raise Exception(('It seems there is a node already running. PID is %d. ' +
                            'If no node with this pid is running, then you may ' +
                            'have to delete the file manually.') % lock.pid)

    def _start_channel_manager_(self):
        if self.channel_manager is not None:
            return self.channel_manager
        aio_srv = self.aio_server or AsyncIOWebSocketServer(host=self.config['server'].get('hostname'),
                                         port=self.config['server']['port'],
                                         web_socket_class=IncomingChannelWSAdapter)

        def start_aio_server():
            self.log.debug('AIO Server start')
            aio_srv.start()
            self.log.debug('AIO Server end')

        th = threading.Thread(target=start_aio_server)
        th.start()
        channel_manager = ChannelManager(aio_srv)
        self.aio_server = aio_srv
        self.log.debug('AIO Server set up')
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
                self.lock.debug('Message ', message_str)
        self.channel_manager.on('channel.data', on_channel_data)

    def _build_store_(self):
        store = InMemorySyncedStore(root_path=self.config['store']['path'])
        return store

    def _start_stats_tracker_(self):
        self.stats_tracker = self.stats_tracker or StatsTracker(period=self.config['stats']['update_interval'])
        self.log.info('stats tracking ON')

    def _start_sync_manager_(self):
        self.sync_manager = self.sync_manager or SyncManager(node=self, channel_manager=self.channel_manager,
                                        event_processor=None, sync_interval=10000, sync_percent=0.3)
        self.sync_manager.start()

        neighbours = self.config.get('neighbours')
        if neighbours:
            for url in neighbours:
                name, sep, endpoint = url.partition(':')
                node = NodeInfo(name=name, stats=None, apps=None, endpoint=endpoint)
                self.sync_manager.register_node(node)
                self.log.debug('Added neighbour %s [%s]' % (name, endpoint))

    def __register_to_local(self):
        if self.config.get('lock'):
            endpoint = self.aio_server.get_server_endpoint()
            self.lock.set_info('url', endpoint)

    def __register_command_handlers(self):
        @bus.subscribe('task')
        def __on_task__(task, inc_channel):
            try:
                run = self.runner.run(build_task(task))
                # FIXME: Add context to runner.
                self.__reply(task, run.id, inc_channel)
            except Exception as e:
                self.log.exception('Failed to run task %s', task)
                self.__reply(task, str(e), inc_channel, error=True)

        @bus.subscribe('command')
        def __on_command__(command, inc_channel):
            self.log.debug('Received command: %s over channel %s' % (command, inc_channel))
            self.__process_command(command, inc_channel)

    def __register_commands(self):
        self.command_handler('apps', self.__list_apps)
        self.command_handler('info', self.__get_info)
        self.command_handler('task-result', self.__task_result)
        self.command_handler('run-app', self.__run_app)

    def __run_app(self, command):
        print('RUN APP COMMAND RECEIVED: %s' % command)
        print("RUN APP %s" % command.data['app'])
        return self.run_app(app_name=command.data['app'])

    def __list_apps(self, command):
        return self.get_available_apps()

    def __get_info(self, command):
        return self.get_node_info()

    def __task_result(self, command):
        stats = self.runner.stats
        task_id = command.data['task-id']
        status = stats.get(task_id)
        if not status:
            raise Exception('No such task')
        if status['status'] is not 'DONE':
            raise Exception('Task status %s' % status['status'])
        run = self.runner.tasks[task_id]
        self.log.debug('Task result: [%s]' % run.task.result)
        return run.task.result

    def command_handler(self, command, handler):
        self.commands[command] = handler

    def __process_command(self, command, channel):
        handler = self.commands.get(command.headers['command'])
        if not handler:
            self.__reply(command, reply='Unknown command', error=True, channel=channel)
            return
        try:
            reply = handler(command)
            self.__reply(command, reply=reply, channel=channel)
        except Exception as e:
            self.__reply(command, reply=str(e), error=True, channel=channel)
            logging.exception('Failed to execute command %s', command)

    def __reply(self, msg, reply, channel, error=None):
        reply_msg = message().header('reply-for', msg.id).\
            header('type', 'reply').\
            value('error', error).value('reply', reply).build()
        ser_msg = serialize(reply_msg)
        channel.send(ser_msg)

    def _merge_apps(apps, napps, node):
        for napp in napps:
            app = apps.get(napp.name)
            if not app:
                app = {
                    'name': napp.name,
                    'description': napp.description,
                    'command': napp.command,
                    'params': napp.params,
                    'needs': napp.needs,
                    'nodes': []
                }
                apps[napp.name] = app
            app['nodes'].append(node)

    def get_available_apps(self):
        apps = {}
        Node._merge_apps(apps, self.get_apps(), self.get_node_info())

        for node_name, node_info in self.sync_manager.known_nodes.items():
            if node_name is not self.node_id:
                Node._merge_apps(apps, node_info.apps, node_info)
        return apps

    def get_stats(self):
        pass

    def get_apps(self):
        return [app for name, app in self.store.apps.items()]

    def query(self, q):
        pass

    def run_app(self, app_name):
        # find app
        # sort nodes by requirements
        apps = self.get_available_apps()

        app = apps.get(app_name)
        if not app:
            raise Exception('No such app %s' % app_name)

        ranked = Node._rank_nodes(app['needs'], app['nodes'])
        for ranked_node in ranked:
            try:
                return self._run_as_task(app, ranked[0])
            except Exception as e:
                logging.exception('Failed to run on node %s' % ranked_node)
        raise Exception('Failed to run app %s'%app_name)

    def _run_as_task(self, app, ranked_node):
        remote = ranked_node['node'] != self.node_id
        node = {'name': ranked_node['node']}

        if remote:
            node_info = self.sync_manager.get_node_info(ranked_node['node'])
            node['host'] = node_info.hostname
            node['port'] = node_info.data['ssh'].get('port') or 22
            node['ssh_user'] = node_info.data['ssh'].get('user') or 'root'

        task = task_for_app(app=app, remote=remote, node=node)
        return self.runner.run(task)

    def _rank_nodes(app_needs, nodes_info):
        m = max([v for k,v in app_needs.items()])
        W = {}
        for k, v in app_needs.items():
            W[k] = v/m

        return sorted([{'score': Node._calc_score(node_info.stats, W), 'stats': node_info.stats, 'node': node_info.name} for node_info in nodes_info], key=lambda x: x['score'], reverse=True)

    def _calc_score(stats, W):
        score = 0
        # CPU score
        score += Node._relevant_cpu_value(stats) * W['cpu']
        score += stats.memory['available'] * W['memory']
        score += stats.disk['ioload'] * (-W['disk'])
        # FIXME: add network score
        return score

    def _relevant_cpu_value(stats):
        # available bogomips = total bogomips - cpu usage * total bogomips = total bogomips * (1 - cpu usage)
        total_bogomips = stats.cpu['bogomips']['total']
        usage = stats.cpu['usage']
        return total_bogomips * (1 - usage)

    def start(self):
        if self.config.get('lock'):
            self.__lock()
        self.channel_manager = self._start_channel_manager_()
        self.log.info('Node %s started' % self.node_id)
        self._start_stats_tracker_()
        self._start_sync_manager_()
        self.__register_message_dispatcher__()
        self.__register_to_local()
        self.__register_command_handlers()

    def stop(self):
        self.log.debug('node stop')
        if self.stats_tracker:
            self.stats_tracker.stop_tracking()
            self.log.info('Statistics tracking has stopped')
        if self.aio_server:
            self.aio_server.stop()
            self.log.info('Async I/O Server notified to stop')
        if self.sync_manager:
            self.sync_manager.stop()
        if self.lock:
            self.lock.unlock()
        self.runner.shutdown()
        self.log.debug('Runner stopped')

    def get_node_info(self):
        return NodeInfo(name=self.node_id, stats=self.stats_tracker.get_stats(),
                        apps=self.get_apps(), endpoint=self.aio_server.get_server_endpoint(),
                        hostname=self.stats_tracker.hostname)


class NodeInfo:
    def __init__(self, name=None, stats=None, apps=None, endpoint=None, hostname=None, data=None):
        self.name = name
        self.stats = stats
        self.apps = apps
        self.endpoint = endpoint
        self.hostname = hostname
        self.data = data or {}


def node_info_from_dict(node_dict):
    apps = []
    dapps = node_dict.get('apps') or []

    for dapp in dapps:
        app = deserialize_dict(dapp, App)
        apps.append(app)

    dstats = node_dict.get('stats') or {}
    stats = deserialize_dict(dstats, SystemStats)
    node = deserialize_dict(node_dict, NodeInfo)
    node.apps = apps
    node.stats = stats
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
        self.event_processor = event_processor
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
                logging.info('Node %s has joined' % node.name)
                self._print_known_nodes_()
            self._merge_node_(node)

    def _print_known_nodes_(self):
        logging.debug(' Members: ')
        for name, node in self.known_nodes.items():
            logging.debug('   %s[%s]' % (name, node.endpoint))

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
            logging.info('Node %s has probably left' % name)

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
                logging.debug('Sync with %s [%s]' % (name, node.endpoint))
                try:
                    self.channel_manager.send(to_url=node.endpoint, data=serialize(self.get_sync_message(), indent=2))
                except ChannelClosedError as e:
                    pass
                except Exception as e:
                  raise

    def sync_one_node(self, node, this_node_info):
        pass

    def get_sync_message(self):
        return message().value('node', self.node.get_node_info()).\
            value('known_nodes', [n for k, n in self.known_nodes.items()]).\
            header('type', 'sync-message').build()

    def get_node_info(self, node):
        node_info = self.known_nodes.get(node)
        if not node_info:
            raise Exception('Unknown node %s' % node)
        return node_info


NODE_LOCK_FILE_PATH = '/tmp/troup.node.lock'


def local_node_lock_file(node_info=None):
    return this_process_info_file(NODE_LOCK_FILE_PATH, info=node_info, create=True)


def check_local_node_lock():
    return open_process_lock_file(NODE_LOCK_FILE_PATH)


def read_local_node_lock():
    return open_process_lock_file(NODE_LOCK_FILE_PATH, read_only=True)
