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

import psutil
import os
import platform

from troup.threading import IntervalTimer

class SystemStats:
    """Statistics values for the underlying system.
    
    Holds the values for a single measurement of the system performance.
    
    Attributes:
        cpu (dict): Holds the CPU values in a dictionary. The following values 
            are retrieved: 
            * "usage" (number): CPU usage. It is a number 0.0 - 1.0.
            * "per_cpu" (Array[number]): CPU usage per CPU. Reports the usage of each
                CPU separately in an Array.
            * "processors" (int): Number of processors present on the system.
            * "bogomips" (number): Bogus MIPS as reported by the Linux kernel (if available)
        memory (dict): Holds the values for the system memory:
            * "total" (int): total memory present in the system in Bytes.
            * "user" (int): Used memory (in Bytes).
            * "free" (int): Free memory (in Bytes).
        system (dict): System load and general system info:
            * "load" (Array[number]): System load as reported by the system. Usually this 
                is an array of three values - the system load for the last 5, 10 and 15 minutes.
            * "name" (str): Node name or the name of the machine.
            * "platform" (str): The underlying OS platform. May be "linux", "bsd" etc.
        disk (dict): Information about the disk and I/O of the system:
            * "ioload" (number): Normalized Input/Output load of the system - a number
                between 0.0 and 1.0. This is the average value for the disk usage in a 
                previous time interval.
    """

    def __init__(self):
        self.cpu = {'usage': 0.0, "per_cpu": [], 'processors': 0, 'bogomips': 0}
        self.memory = {'total': 0, 'used': 0, 'available': 0}
        self.system = {'load': [0.0, 0.0, 0.0], 'name': '', 'platform': ''}
        self.disk = {'ioload': 0.0}
                

class StatsTracker:

    def __init__(self, period=1000):
        self.period = period
        self.cpu_usage = []
        self.cpu_usage_avg = psutil.cpu_percent()/100
        self.cpu_count = psutil.cpu_count()
        self.hostname = platform.node()
        self.platform = platform.system()
        self.periodic_update = IntervalTimer(interval=self.period, target=self.refresh_values)
        self.periodic_update.start()
    
    def refresh_values(self):
        cpu_usage = psutil.cpu_percent(percpu=True)
        self.cpu_usage = [usage/100 for usage in cpu_usage]
    
    def get_stats(self):
        stats = SystemStats()
        
        stats.cpu = self._get_cpu_stats_()
        stats.memory = self._get_mem_stats_()
        stats.system = self._get_system_stats_()
        stats.disk = self._get_disk_stats_()
        
        return stats
    
    def _get_disk_stats_(self):
        stats = {
            'ioload': 0.0
        }
        
        return stats
    
    def _get_cpu_stats_(self):
        stats = {
            'usage': self.cpu_usage_avg,
            'per_cpu': self.cpu_usage,
            'processors': self.cpu_count,
            'bogomips': 0.0 # FIXME: read from proc
        }
        return stats
    
    def _get_mem_stats_(self):
        mem = psutil.virtual_memory()
        stats = {
            'total': mem.total,
            'used': mem.used,
            'available': mem.available
        }
        return stats
    
    def _get_system_stats_(self):
        stats = {}
        one, five, fifteen = os.getloadavg()
        stats['load'] = [one, five, fifteen]
        
        return stats
    
    def stop_tracking(self):
        self.periodic_update.cancel()



if __name__ == '__main__':
    import json
    import time
    
    tracker = StatsTracker(period=1000)
    
    while(True):
        s = tracker.get_stats()
        print(json.dumps(s.__dict__, indent=2))
        time.sleep(1)