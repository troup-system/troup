from argparse import ArgumentParser
from appliance.node import Node

def configure_node_parser():
    parser = ArgumentParser(prog='appliance', description='Run single node')
    
    # Node
    parser.add_argument('--node', help='Node ID')
    
    # Async IO server props
    parser.add_argument('--host', default='', help='Async IO server hostname')
    parser.add_argument('--port', default=7000, help='Async IO server port')
    
    # Store
    parser.add_argument('--storage-root', default='.data', help='Root path of the storage directory')
    
    parser.add_argument('-v', '--version', action='store_true', help='Print version and exit')
    
    return parser
    

def run_node():
    parser = configure_node_parser()
    args = parser.parse_args()
    
    if args.version:
        print('0.0.1')
        return
    config = {
        'store':{
            'path': args.storage_root
        },
        'server':{
            'hostname': args.host,
            'port': args.port
        }
    }
    node = Node(node_id=args.node, config=config)
    
    node.start()
    
    print('Started')
    
