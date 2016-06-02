from argparse import ArgumentParser
from troup.node import Node
import logging


def configure_node_parser():
    parser = ArgumentParser(prog='troup', description='Run single node')
    
    # Node
    parser.add_argument('--node', help='Node ID')
    parser.add_argument('--neighbours', default='', nargs='+', help='Neighbour nodes')
    
    # Async IO server props
    parser.add_argument('--host', default='', help='Async IO server hostname')
    parser.add_argument('--port', default=7000, help='Async IO server port')
    
    # Store
    parser.add_argument('--storage-root', default='.data', help='Root path of the storage directory')
    
    # System statistics
    parser.add_argument('--stats-update-interval', default=30000, help='Statistics update interval in milliseconds')
    
    parser.add_argument('--log-level', '-l', default='info', help='Logging level')

    parser.add_argument('--lock', action='store_true', help='Write node info in global lock file')

    parser.add_argument('--debug', action='store_true', help='Activate the debug command-line interactive interface')

    parser.add_argument('-v', '--version', action='store_true', help='Print version and exit')
    
    return parser
    

def run_node():
    import signal
    
    parser = configure_node_parser()
    args = parser.parse_args()
    
    if args.version:
        print('0.0.1')
        return
        
    logging.basicConfig(level=getattr(logging, args.log_level.upper()))
    
    config = {
        'store': {
            'path': args.storage_root
        },
        'server': {
            'hostname': args.host,
            'port': args.port
        },
        'stats': {
            'update_interval': args.stats_update_interval
        },
        'neighbours': args.neighbours,
        'lock': args.lock
    }
    node = Node(node_id=args.node, config=config)
    
    def handle_node_shutdown(signal, frame):
        node.stop()
    
    signal.signal(signal.SIGINT, handle_node_shutdown)

    if args.debug:
        from troup.debug import run_debug_cli
        run_debug_cli()

    node.start()
    
    return node