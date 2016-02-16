__author__ = 'pavle'

import psutil
import os

from appliance.threading import IntervalTimer

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
        self.memory = {'total': 0, 'used': 0, 'free': 0}
        self.system = {'load': [0.0, 0.0, 0.0], 'name': '', 'platform': ''}
        self.disk = {'ioload': 0.0}
                

class StatsTracker:

    def __init__(self, period=1000):
        self.period = period
        self.cpu_usage = []
        self.cpu_usage_avg = psutil.cpu_percent()/100
        self.cpu_count = psutil.cpu_count()
        self.periodic_update = IntervalTimer(interval=self.period, target=self.refresh_values)
        self.periodic_update.start()
    
    def refresh_values(self):
        cpu_usage = psutil.cpu_percent(interval=self.period/1000,percpu=True)
        self.cpu_usage = [usage/100 for usage in cpu_usage]
    
    def get_stats(self):
        stats = SystemStats()
        stats.cpu['usage'] = self.cpu_usage.avg
        stats.cpu['per_cpu'] = self.cpu_usage
        stats.cpu['processors'] = self.cpu_count
        stats.cpu['bogomips'] = 0.0 # FIXME: read from proc
        
        
        return stats
    
    def stop_tracking(self):
        self.periodic_update.cancel()



if __name__ == '__main__':
    import psutil
    import os

    print("CPU usage: %s"%str(psutil.cpu_percent()))
    print("Mem usage: %s"%(str(psutil.virtual_memory())))
    print("CPUs count: %d"%psutil.cpu_count())
    print("CPU usage (per cpu): %s"%psutil.cpu_percent(percpu=True))
    print("System load: %s" % str(os.getloadavg()))
    print("IO (for /): %s" % str(psutil.disk_io_counters()))

    cps = psutil.cpu_percent(interval=0.5,percpu=True)
    print(cps)
