import unittest
import sys

sys.path.append('..')

from troup.testtools import expect_content
from troup.store import InMemorySyncedStore
from troup.apps import App


class InMemorySyncStoreTest(unittest.TestCase):
    
    def setUp(self):
        self.store = InMemorySyncedStore(root_path='tests/resources/store', \
                                        apps_file='test_add_app.json',\
                                        settings_file='test_add_app.settings.json')
    
    @expect_content(file='tests/resources/store/test_add_app.json', \
                    expect_file='tests/resources/store/test_add_app.expected.json', \
                    content_type='json')
    def test_add_app(self):
        app = App(name='test-app', description='description', command='run test-app',\
                 params={'p1':'v1', 'p2':'v2'},\
                 needs={'cpu': 0, 'memory': 1, 'network': 2, 'disk': 3})
        self.store.add_app(app)
