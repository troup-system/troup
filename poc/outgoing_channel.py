import sys
import time
import threading

sys.path.append('..')

print(sys.path)

from appliance.infrastructure import OutgoingChannelOverWS

oc = OutgoingChannelOverWS('tc', 'ws://localhost:8910')


class RunAlone(threading.Thread):
    def run(self):
        oc.connect()
        

a = RunAlone()
a.start()
time.sleep(10)
print('Done')



