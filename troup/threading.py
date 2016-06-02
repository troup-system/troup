from threading import Timer, Condition


class AtomicOperation:

    def __init__(self):
        self.lock = Condition()

    def op(self):
        with self.lock:
            return self.atomic_op()

    def atomic_op(self):
        pass


class AtomicIncrement(AtomicOperation):

    def __init__(self, initial_value=0):
        self._int_val = initial_value
        super(AtomicIncrement, self).__init__()

    def atomic_op(self):
        self._int_val += 1

    def inc(self):
        return self.op()

    @property
    def value(self):
        return self._int_val

    def __repr__(self):
        return '%d' % self._int_val

    def __str__(self):
        return self.__repr__()

_id_inc = AtomicIncrement()


def _next_id(pref):
    _id_inc.inc()
    return '%s-%s' %(pref, _id_inc)


class IntervalTimer:
    
    def __init__(self, interval, offset=0, target=None, name=None):
        self.target = target
        self.timer = None
        self.running = False
        self.offset = offset
        self.interval = interval
        self.first = True
        self.name = name or _next_id('IntervalTimer')
        
    def start(self):
        if self.running:
            return
        interval = self.interval
        if self.first:
            interval = interval + self.offset
            self.first = False
        self._run_()

    def cancel(self):
        if self.timer:
            self.timer.cancel()
            self.running = False

    def _run_(self):
        self.running = True
        self.timer = Timer(self.interval/1000, self._run_)
        self.timer.name = self.name
        self.timer.start()
        self.run()
        self.running = False
    
    def run(self):
        if self.target:
            self.target()