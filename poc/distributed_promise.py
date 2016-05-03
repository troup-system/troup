import sys

sys.path.append('..')
print(sys.path)
import troup
from troup.distributed import Promise

import time
import threading

promise = Promise()

def producer():
    time.sleep(2)
    promise.complete(result="Yay!")
    print('Produced result')

def consumer():
    result = promise.result
    print('Got result: %s' % result)

tp = threading.Thread(target=producer)
tc = threading.Thread(target=consumer)

tc.start()
tp.start()

time.sleep(5)
print('exit')
