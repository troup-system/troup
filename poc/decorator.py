class decorate:
    def __init__(self, arg1=None, arg2=None):
        self.arg1 = arg1
        self.arg2 = arg2
    
    def __call__(self, method):
        def wrapper():
            print('ARG1 = %s, ARG2 = %s' % ( str(self.arg1), str(self.arg2)) )
            method()
        return wrapper
@decorate('the decoration', 34)
def test():
    print('test method')

test()
