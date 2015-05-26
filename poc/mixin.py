class A:
    def __init__(self):
        print('A init')

class M1(A):
    def __init__(self):
        super(M1, self).__init__()
        print('M1 init')

class M2(A):
    def __init__(self):
        super(M2, self).__init__()
        print('M2 init')

class R1(M2, M1):
    def __init__(self):
        super(R1, self).__init__()
        print('R1 init')
        
r = R1()
