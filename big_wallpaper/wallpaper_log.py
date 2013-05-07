import logging
import sys

def getLogger():
    return sys.modules['__main__'].logger;

class WallPaperLog:

    def __init__(self, path='/tmp/big_wallpaper.log'):
        logging.basicConfig(filename=path, format='%(asctime)s %(levelname)s:%(message)s', datefmt='%Y/%m/%d %I:%M:%S %p', level=logging.DEBUG)

    def log(self, msg, level='info'):
        print msg
        if level == 'info':
            logging.info(msg)
        elif level == 'warning':
            logging.warning(msg)
        elif level == 'debug':
            logging.debug(msg)
        elif level == 'error':
            logging.error(msg)
        elif level == 'critical':
            logging.critical(msg)
