from threading import Timer

class IntervalTimer:
    
    def __init__(self, interval, offset=0, target=None):
        self.target = target
        self.timer = None
        self.running = False
        self.offset = offset
        self.interval = interval
        self.first = True
        
    def start(self):
        if self.running:
            return
        interval = self.interval
        if self.first:
            interval = interval + self.offset
            self.first = False
        self.timer = Timer(interval/1000, self._run_)
        
        
    def cancel(self):
        if self.timer:
            self.timer.cancel()
            self.running = False
    
    
    def _run_(self):
        self.running = True
        self.run()
        self.running = False
    
    def run(self):
        if self.target:
            self.target()
    
