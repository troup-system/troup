from troup.infrastructure import OutgoingChannelOverWS



class ChannelClient:

    def __init__(self, nodes_specs=None, reply_timeout=5000):
        self.nodes_ref = {}
        self.channels = {}

        self.__build._nodes_refs__(nodes_specs)

    def __build_nodes_refs__(self, nodes_specs):
        for spec in nodes_specs:
            parsed = spec.partition(':')
            self.nodes_ref[parsed[0]] = parsed[2]

    def send_message(self, message, to_node=None, on_reply=None):
        def reply_callback_wrapper(*args, **kwargs):
            if on_reply:
                on_reply(*args, **kwargs)

        if to_node:
            self.send_message_to_node(message, to_node, reply_callback_wrapper)
        else:
            for name, node in self.nodes_ref.items():
                self.send_message_to_node(message, node, reply_callback_wrapper)

    def send_message_to_node(self, message, node, on_reply):
        channel = self.get_channel(node)
        channel.send(message)


    def get_channel(self, for_node):
        channel = self.channel.get(for_node)
        if not channel:
            channel = self.build_channel(for_node)
        return channel

    def build_channel(self, for_node):
        ref = self.nodes_ref.get(for_node)
        if not ref:
            raise Exception('Unknown node reference [%s]' % for_node)
        return self.create_channel(for_node, ref)

    def create_channel(node_name, reference):
        return OutgoingChannelOverWS(node_name, reference)



class CommandAPI:

    def __init__(self, channel_client):
        self.channel_client = channel_client

    def send_command(self, command, to_node=None, on_reply=None):
        pass

    def monitor(self, command_ref):
        pass

    def command(self, name, data):
        pass
