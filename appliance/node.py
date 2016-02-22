__author__ = 'pavle'

from appliance.store import InMemorySyncedStore
from appliance.infrastructure import AsyncIOWebSocketServer, IncomingChannelWSAdapter, ChannelManager
from appliance.system import StatsTracker
from appliance.messaging import message
import threading


class Node:

    def __init__(self, node_id, config):
        self.node_id = node_id
        self.config = config
        self.store = self._build_store_()
        self.channel_manager = None
        self.aio_server = None
        self.stats_tracker = None
    
    def _start_channel_manager_(self):
        aio_srv = AsyncIOWebSocketServer(host=self.config['server'].get('hostname'), port=self.config['server']['port'], web_socket_class=IncomingChannelWSAdapter)
        def start_aio_server():
            aio_srv.start()
        th = threading.Thread(target=start_aio_server)
        th.start()
        print('1')
        channel_manager = ChannelManager(aio_srv)
        self.aio_server = aio_srv
    
    def _build_store_(self):
        store = InMemorySyncedStore(root_path=self.config['store']['path'])
        return store
    
    def _start_stats_tracker_(self):
        self.stats_tracker = StatsTracker(period=self.config['stats']['update_interval'])
        print('stats tracking ON')
    
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
        self.channel_manager = self._start_channel_manager_()
        print('Node %s started' % self.node_id)
        self._start_stats_tracker_()

    def stop(self):
        print('node stop')
        if self.stats_tracker:
            self.stats_tracker.stop_tracking()
            print('Statistics tracking has stopped')
        if self.aio_server:
            self.aio_server.stop()
            print('Async I/O Server notified to stop')
    
    def get_node_info(self):
        pass
      

class NodeInfo:
    self __init__(self, name, stats, apps, endpoint):
        self.name = name
        self.stats = stats
        self.apps = apps
        self.endpoint = endpoint

class EventProcessor:
    def __init__(self, node):
        self.node = node
        self.handlers = {}
    
    def process(self, event, message):
        handlers = self.handlers.get(event)
        if handlers:
            for handler in handlers:
                handler(message, event, self)
    
    def register_handler(self, event_name, handler):
        handlers = self.handlers.get(event_name)
        if not handlers:
            handlers = self.handlers[event_name] = []
        handlers.append(handler)


class SyncManager:
    
    def __init__(self, node, channel_manager, event_processor):
        self.node = node
        self.channel_manager = channel_manager
        self.event_processor= event_processor
        self.known_nodes = {}
    
    def start(self):
        pass
        
    def stop(self):
        pass
    
    def register_node(self, node):
        pass
    
    def unregister_node(self, node):
        pass
        
    def sync_random_nodes(self):
        pass
        
    def sync_one_node(self, node, this_node_info):
        pass
    
    def get_sync_message(self):
        return message().value('node', self.node.get_node_info()).
            value('known_nodes', [n for k,n in self.known_nodes.items()]).
            .value('type', 'sync-message').build()
    
    
