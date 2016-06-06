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

class Observable:
    
    def __init__(self):
        self.listeners = {}
    
    def on(self, event, handler):
        listeners = self.listeners.get(event)
        if not listeners:
            listeners = self.listeners[event] = []
        listeners.append(handler)
    
    def trigger(self, event, *args):
        listeners = self.listeners.get(event)
        if listeners:
            for listener in listeners:
                listener(*args)
    
    def remove_listener(self, event, listener):
        listeners = self.listeners.get(event)
        if listeners:
            listeners.remove(listener)
