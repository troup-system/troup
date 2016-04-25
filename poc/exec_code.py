def test_fn(a,b,c):
    print('%d' %(a+b-c))

import inspect

print(inspect.getsource(test_fn))
