__author__ = 'pavle'

from appliance.store import InMemorySyncedStore
from appliance.infrastructure import AsyncIOWebSocketServer, IncomingChannelWSAdapter, ChannelManager
from appliance.system import StatsTracker
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

    def register_remote_node(self, node_id, host, port):
        pass

    def unregister_remote_node(self, node_id):
        pass

    def sync_with(self, node_id):
        pass

    def sync_with_all(self):
        pass
      
        
class SyncManager:
    
    def __init__(self, channel_manager):
        self.channel_manager = channel_manager
        self.known_nodes = []
    
