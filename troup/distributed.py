from threading import Condition

class Promise:
    def __init__(self):
        self.error = None
        self.__result = None
        self.__is_done = False
        self.__cw = Condition()

    @property
    def result(self):
        while not self.__is_done:
            self.wait()

        if self.error:
            raise DistributedException(self.error, self.__result)
        return self.__result

    @propery
    def is_done(self):
        return self.__is_done

    def complete(self, result=None, error=None):
        self.__is_done = True
        self.error = error
        self.result = result
        self.__cw.notify_all()



class DistributedException(Exception):

    def __init__(self, message, data=None):
        super(DistributeException, self).__init__(message)
        self.data = data
