import logging


class Logger:
    def __init__(self, level='debug'):
        logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                            datefmt='%H:%M:%S')

        logger = logging.getLogger(__name__)
        levels = {
            'info': logging.INFO,
            'warning': logging.WARNING,
            'error': logging.ERROR,
            'debug': logging.DEBUG,
        }
        logger.setLevel(levels[level])
        self.logger = logger

def get_logger(level='debug'):
    return Logger(level=level).logger