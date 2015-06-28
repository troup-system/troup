import sys

sys.path.append('..')

print(sys.path)

from appliance.infrastructure import OutgoingChannelOverWS

oc = OutgoingChannelOverWS('tc', 'ws://localhost:8910')

oc.connect()

