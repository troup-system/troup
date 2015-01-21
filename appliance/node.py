__author__ = 'pavle'


class Node:

    def __init__(self, node_id, config):
        self.node_id = node_id
        self.config = config

    def get_available_apps(self):
        pass

    def get_stats(self):
        pass

    def run_app(self, app_name):
        pass

    def start(self):
        pass

    def stop(self):
        pass

    def register_remote_node(self, node_id, host, port):
        pass

    def unregister_remote_node(self, node_id):
        pass

    def sync_with(self, node_id):
        pass

    def sync_with_all(self):
        pass