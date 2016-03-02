import random

class TestSyncManager:
    
    def __init__(self):
        self.nodes = ['a','b','c','d','e','f']
        self.random_buffer = []
        self.shuffle_all()
    
    def shuffle_all(self):
        nodes = [] + self.nodes
        random.shuffle(nodes)
        self.random_buffer = self.random_buffer + nodes
        return self.random_buffer
    
    def next(self, n):
        while len(self.random_buffer) < n:
            self.shuffle_all()
        shuffled = self.random_buffer[0:n]
        self.random_buffer = self.random_buffer[n:]
        return shuffled
                
tm = TestSyncManager()

for i in range(1, 10):
    #print('--------------')
    #print('before: ' + str(tm.random_buffer))
    print(tm.next(40))
    #print('after:  ' + str(tm.random_buffer))
    
