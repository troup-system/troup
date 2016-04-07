from troup.infrastructure import OutgoingChannelOverWS



class Client:
    
    def __init__(self, nodes_specs=None):
        self.nodes_ref = {}
        self.channels = {}
        
        self.__build._nodes_refs__(nodes_specs)
    
    def __build_nodes_refs__(self, nodes_specs):
        for spec in nodes_specs:
            parsed = spec.partition(':')
            self.nodes_ref[parsed[0]] = parsed[2]
    
    def send_command(self, command, to_node=None, on_reply=None):
        pass
    
    def send_command_to_node(self, command, node, on_reply):
        pass
    
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
        pass
    
    
    
