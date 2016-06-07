import sys

sys.path.append('..')

from troup.process import SSHRemoteProcess

rp = SSHRemoteProcess(id="xterm-01", name="xterm", args=[], cwd="/home/pavle", target_host="natemago", target_port="7799", ssh_user="pavle", forward_video=True)

import time

rp.execute()

time.sleep(10)
