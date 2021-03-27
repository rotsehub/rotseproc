import logging

class rotseLogger:
    """
    Simple logger class using logging
    """
    __loglvl__ = None
    __loggername__ = "ROTSE-III"
    def __init__(self, name=None, loglevel=logging.INFO):
        if name is not None:
            self.__loggername__=name
        if rotseLogger.__loglvl__ is None:
            rotseLogger.__loglvl__=loglevel
        self.__loglvl__ = rotseLogger.__loglvl__
        format = '%(asctime)-15s %(name)s %(levelname)s : %(message)s'
        logging.basicConfig(format=format, level=self.__loglvl__)
    def getlog(self, name=None):
        if name is None:
            loggername = self.__loggername__
        else:
            loggername = name
        return logging.getLogger(loggername)

