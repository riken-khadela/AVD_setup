import logging
import sys
import os
import inspect
from logging import handlers

def get_caller_file_name():
    # frame = inspect.stack()[1]
    frame = inspect.stack()[-1]
    module = inspect.getmodule(frame[0])
    # return module.__name__

    # index = -2
    # while not module:
        # frame = inspect.stack()[index]
        # module = inspect.getmodule(frame[0])
        # index -= 1

    # print(module)

    if module:
        module_full_path_name = os.path.splitext(os.path.abspath(module.__file__))[0] + '.log'
        module_name = os.path.splitext(os.path.basename(module.__file__))[0]
    else:
        module_full_path_name = ''
        module_name = '__main__'
    return [module_name, module_full_path_name]

class Log(object):
    def __init__(self, log_file=get_caller_file_name()[1], log_name=get_caller_file_name()[0], 
            log_level=logging.INFO):
        self.log_name = log_name
        self.log_file = log_file
        self.log_level = log_level
        self.handler_level = self.log_level

        # create formatter
        # self.formatter = logging.Formatter('%(asctime)s  %(filename)s  %(levelname)-8s %(message)s')
        self.formatter = logging.Formatter('%(asctime)s  %(filename)s  %(name)s\t %(levelname)-8s %(message)s')
        # print('log_name: %s' % log_name)
        # print('log_file: %s' % log_file)

    @property 
    def console_handler(self):
        handler = logging.StreamHandler()
        handler.setLevel(self.handler_level)
        handler.setFormatter(self.formatter)
        return handler

    @property 
    def console_logger(self):
        log = logging.getLogger(self.log_name+'.console')
        log.setLevel(self.log_level)
        log.addHandler(self.console_handler)
        return log

    @property 
    def rotating_file_handler(self):
        if not self.log_file:
            return None
        handler = handlers.RotatingFileHandler(self.log_file)
        handler.setLevel(self.handler_level)
        handler.setFormatter(self.formatter)
        return handler

    @property 
    def rotating_file_logger(self):
        log = logging.getLogger(self.log_name+'.rotatingfile')
        log.setLevel(self.log_level)
        log.addHandler(self.rotating_file_handler)
        return log


    @property 
    def timed_rotating_file_handler(self):
        if not self.log_file:
            return None
        handler = handlers.TimedRotatingFileHandler(self.log_file, 'D')
        handler.setLevel(self.handler_level)
        handler.setFormatter(self.formatter)
        return handler

    @property 
    def timed_rotating_file_logger(self):
        log = logging.getLogger(self.log_name+'.timedrotatingfile')
        log.setLevel(self.log_level)
        log.addHandler(self.timed_rotating_file_handler)
        return log

    @property
    def logger(self):
        log = logging.getLogger(self.log_name)
        log.setLevel(self.log_level)
        log.addHandler(self.console_handler)
        if self.rotating_file_logger:
            log.addHandler(self.rotating_file_handler)
        return log

if __name__ == '__main__':
    logger = Log().logger
    logger.debug('debug message')
    logger.info('info message')
    logger.warn('warn message')
    logger.error('error message')
    logger.critical('critical message')

