__author__ = 'pavle'


class SystemStats:
    """
    Stats:
        - cpu usage
        - memory usage
        - total number of physical CPUs
        - usage per CPU
        - system load
        - io load
    """

    def __init__(self):
        self.cpu = {'usage': 0.0, 'processors': 1, 'bogomips': 1}
        self.memory = {'total': 1, 'used': 1, 'free': 1}
        self.system = {'load': [0.0, 0.0, 0.0], 'name': ''}
        self.disk = {'ioload': 0.0}
                


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