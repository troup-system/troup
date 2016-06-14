import unittest
import sys

sys.path.append('..')

from troup.system import get_bogomips


class GetBogomipsTest(unittest.TestCase):
    
    def test_get_bogomips(self):
        bogomips = get_bogomips()
        assert bogomips
        print(bogomips)
