import logging

class WallPaperLog:

    _instance = None;

    @staticmethod
    def init(cls,path):
        logging.basicConfig(filename=path, format='%(asctime)s %(levelname)s:%(message)s', datefmt='%Y/%m/%d %I:%M:%S %p', level=logging.DEBUG)
        cls._instance = logging

    @staticmethod
    def getInstance(cls):
        if cls._instance is None:
            logging.basicConfig(filename='/tmp/big_wallpaper.log', format='%(asctime)s %(levelname)s:%(message)s', datefmt='%Y/%m/%d %I:%M:%S %p', level=logging.DEBUG)
            cls._instance = logginig
        return cls._instance

    def __init__(self):
        pass
