import unittest
from unittest.mock import Mock, MagicMock, patch
import sys

sys.path.append('..')

from troup.node import Node
from troup.testtools import load_content


class AppsRankingTest(unittest.TestCase):

    @load_content('tests/resources/node/rank_nodes.nodes_info.json')
    def test_rank_nodes(self, nodes_info):
        app_needs = {
            "disk": 10,
            "memory": 128,
            "network": 0.05,
            "cpu": 500
        }

        known_nodes = []
        for node_id, node_dict in nodes_info.items():
            known_nodes.append(node_info_from_dict(node_dict))

        ranked = Node._rank_nodes(app_needs, known_nodes)
        print(ranked)



from troup.node import Node, node_info_from_dict
from troup.apps import App
from troup.system import SystemStats

class RunAppTest(unittest.TestCase):

    @load_content('tests/resources/node/run_app.nodes_info.json')
    @load_content('tests/resources/node/run_app.dummy_store.json')
    @patch('troup.node.SyncManager')
    @patch('troup.system.StatsTracker')
    @patch('troup.infrastructure.AsyncIOWebSocketServer')
    @patch('troup.infrastructure.ChannelManager')
    @patch('troup.store.Store')
    @patch('troup.tasks.TasksRunner')
    def test_run_app(self, nodes_info, dummy_store_data, Store,
                     ChannelManager, AsyncIOWebSocketServer,
                     StatsTracker, SyncManager,
                     TasksRunner):
        print('Nodes info -> %s' % nodes_info)
        print('Store data -> %s' % dummy_store_data)
        apps = {}
        for app_id, app_json in dummy_store_data.items():
            apps[app_id] = App(name=app_json['name'], description=app_json.get('description'),\
                command=app_json['command'], params=app_json.get('params'),\
                needs=app_json.get('needs'))

        m_store = Store()
        m_store.apps = apps

        m_channel_manager = ChannelManager()
        m_aio_server = AsyncIOWebSocketServer()
        m_stats_tracker = StatsTracker()
        m_sync_manager = StatsTracker()
        m_tasks_runner = TasksRunner()

        known_nodes = {}
        for node_id, node_dict in nodes_info.items():
            known_nodes[node_id] = node_info_from_dict(node_dict)

        m_sync_manager.known_nodes = known_nodes

        m_stats_tracker.get_stats.configure_mock(return_value=SystemStats())

        try:
            node = Node(node_id='test-node', config={}, store=m_store, channel_manager=m_channel_manager,
                        aio_server=m_aio_server, stats_tracker=m_stats_tracker, sync_manager=m_sync_manager,
                        tasks_runner=m_tasks_runner)
            node.start()
            node.run_app('test-app')
        finally:
            node.stop()
