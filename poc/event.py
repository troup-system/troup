import threading
import time

class Consumer(threading.Thread):
    
    def __init__(self, event):
        super(Consumer, self).__init__()
        self.event = event
    
    def run(self):
        print('%s: waiting for event...'%self.name)
        self.event.wait()
        print('%s: got event'%self.name)

class Provider(threading.Thread):
    def __init__(self, event):
        super(Provider, self).__init__()
        self.event = event
        self.timeout = 1000
    
    def run(self):
        print('%s: sleeping for %d ms'%(self.name, self.timeout) )
        time.sleep(self.timeout/1000)
        print('%s: triggering now!' % self.name)
        self.event.set()

ev = threading.Event()

c1 = Consumer(ev)
c2 = Consumer(ev)
c3 = Consumer(ev)

p1 = Provider(ev)

c1.start()
c2.start()
c3.start()
p1.start()

c1.join()
c2.join()
c3.join()
p1.join()


