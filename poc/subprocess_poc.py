import subprocess

pipe = subprocess.Popen(['/usr/bin/python3', 'test-process.py', 'a1', 'a2'], cwd='.')
pipe.wait()
print('Done')
