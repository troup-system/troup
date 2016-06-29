import unittest
import sys

sys.path.append('..')

from troup.node import Node


class AppsRankingTest(unittest.TestCase):
    
    def test_rank_nodes(self):
        app_needs = {
            "disk": 10,
            "memory": 128,
            "network": 0.05,
            "cpu": 500
        }
        
        stats = {
            "n1": {
                "disk": {
                    "ioload": 5
                },
                "memory": {
                    "available": 100
                },
                "cpu": {
                    "bogomips": {
                        "total": 1000
                    },
                    "usage": 0.1
                }
            },
            "n2": {
                "disk": {
                    "ioload": 5
                },
                "memory": {
                    "available": 100
                },
                "cpu": {
                    "bogomips": {
                        "total": 2000
                    },
                    "usage": 0.2
                }
            },
            "n3": {
                "disk": {
                    "ioload": 90
                },
                "memory": {
                    "available": 100
                },
                "cpu": {
                    "bogomips": {
                        "total": 3000
                    },
                    "usage": 0.9
                }
            }
        }
        
        ranked = Node._rank_nodes(app_needs, stats)
        import json
        print(json.dumps(ranked, indent=4))
        
        
