# Copyright 2016 Pavle Jonoski
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import json
from functools import wraps

class expect_content:
    def __init__(self, file=None, expect_file=None, content_type='text'):
        self.file = file
        self.expect_file = expect_file
        self.content_type = content_type
        self.method = None

    def wrapper(self, *args, **kwargs):
        if not self.method:
            return
        self.method(*args, **kwargs)
        with open(self.file) as given:
            with open(self.expect_file) as expected:
                self.compare(given, expected)

    def compare(self, given, expected):
        if self.content_type == 'text':
            compare_text_content(given, expected)
        elif self.content_type == 'json':
            compare_json_content(given, expected)
        else:
            raise Exception('Invalid content type %s' % self.content_type)

    def __call__(self, method):
        self.method = method

        @wraps(method)
        def wrapper(*args, **kwargs):
            return self.wrapper(*args, **kwargs)

        return wrapper

class load_content:

    def __init__(self, path, data_type='json', bound_method=True):
        self.path = path
        self.type = data_type
        self.bound_method = True

    def __call__(self, method):
        @wraps(method)
        def wrapper(*args, **kwargs):
            content = self._load_path()
            nargs = (*args, content)
            method(*nargs, **kwargs)

        return wrapper

    def _load_path(self):
        load_method_name = 'load_%s' % self.type.lower()
        if hasattr(self, load_method_name):
            load_method = getattr(self, load_method_name)
            return load_method()
        else:
            return self.load_default()

    def load_json(self):
        return load_json(self.path)

    def load_default(self):
        with open(self.path) as fs:
            return fs.read()


def compare_text_content(gf, ef):
    given_text = gf.read()
    expected_text = ef.read()
    if given_text != expected_text:
        raise Exception('Text compare failed. Expected [%s] but was given [%s]' %(expected_text, given_text))


def compare_json_content(gf, ef):
    given_json = json.loads(gf.read())
    expected_json = json.loads(ef.read())
    dict_compare(given_json, expected_json)


def list_compare(given, expected):
    if not isinstance(given, list):
        raise Exception('The given object is not list. Expected to get list.')
    if len(given) != len(expected):
        raise Exception('Compare failed. Expected to get list with size %d, but was given list with size %d.' %(len(expected), len(given)))

    i = 0
    for item in expected:
        expected_item = expected[i]
        try:
            if isinstance(item, dict):
                dict_compare(item, expected_item)
            elif isinstance(item, list):
                list_compare(item, expected_item)
            else:
                if item != expected_item:
                    raise Exception('Expected [%s] but was given [%s]' %(expected_item, item))
        except Exception as e:
            raise Exception('Compare failed. List element at index %d: %s' % (i, str(e))) from e
        i += 1

def dict_compare(given, expected):
    if not isinstance(given, dict):
        raise Exception('The given object is not dict. Expected to get dictionary.')
    for key, expected_value in expected.items():
        value = given.get(key)
        try:
            if isinstance(value, dict):
                dict_compare(value, expected_value)
            elif isinstance(value, list):
                list_compare(value, expected_value)
            else:
                if value != expected_value:
                    raise Exception('Expected [%s] but was given [%s]' %(expected_value, value))
        except Exception as e:
            raise Exception('Compare failed. Element for key [%s]: %s' % (key, str(e))) from e


def load_json(file_path):
    with open(file_path) as fl:
        return json.loads(fl.read())
