class Test:
    def __init__(self):
        self.prop1 = None
        raise Exception('Interrupt init')
    def __del__(self):
        print('instance deleted')
        print(self.prop1)

class Test2(Test):
    pass

Test2()
