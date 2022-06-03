import sys
from tblib import pickling_support

@pickling_support.install
class ExceptionWrapper(Exception):

    def __init__(self, ee):
        self.ee = ee
        __, __, self.tb = sys.exc_info()

    def re_raise(self):
        raise self.ee.with_traceback(self.tb)