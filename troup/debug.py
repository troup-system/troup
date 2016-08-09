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

__author__ = 'pavle'

import threading


def print_threads(cmd):
    for th in threading.enumerate():
        print(th)


def print_help(cmd):
    for cmd_name, entry in DBG_HANDLERS.items():
        desc, hnd = entry
        print('%10s - %s' % (cmd_name, desc))


def quit_cli(cmd):
    raise ExitCliException()

class ExitCliException(Exception):
    pass

DBG_HANDLERS = {
    'pt': ('Print Threads', print_threads),
    '?': ('Prints this help message', print_help),
    'help': ('Prints this help message', print_help),
    'q': ('Quits the debug cli', quit_cli),
    'quit': ('Quits the debug cli', quit_cli)
}


def debug_cli():

    while True:
        cmd = input('(debug cli): ')
        cmd = cmd.lower().strip()

        if not cmd:
            continue

        description, handler = DBG_HANDLERS.get(cmd)
        if not handler:
            print('Unrecognized command %d. Type ? for help.')
            continue
        try:
            handler(cmd)
        except ExitCliException:
            break
        except Exception as e:
            print('An error occurred: %s' % e)


def run_debug_cli():
    threading.Thread(target=debug_cli).start()
