#!/usr/bin/env python
# coding=utf-8

import os
import logging
import utils

_INDENT = ''
_INDENT_STEP = 4


class Verbosity(object):

    INFO = 1
    DEBUG = 2
    WARNING = 4
    ERROR = 8
    ALL = 15
    NONE = 0


class _LoggerMockup():

    def info(self):
        pass

    def debug(self):
        pass

    def warning(self):
        pass

    def error(self):
        pass


class _Logger():
    """Logger class. Module's internal usage only.
    """

    verbose = 0
    
    _logger = None
    _log_dir = '%s/log' % os.getcwd()

    def __init__(self):
        """Nothing to see here.
        """

        pass

    @staticmethod
    def _setup_logger():
        """Configure logger.

        Returns:
            logging instance.
        """

        log_format = '%(levelname)-8s %(message)s'

        if not os.path.isdir(_Logger._log_dir):
            os.makedirs(_Logger._log_dir)

        filename = '%s/pyser_%s.log' % (_Logger._log_dir,
                                      utils.get_timestamp())

        logging.basicConfig(level=logging.DEBUG,
                            format=log_format,
                            filename=filename,
                            filemode='w')
    
        if _Logger.verbose:
            console = logging.StreamHandler()
            console.setLevel(logging.DEBUG)
            console.setFormatter(logging.Formatter(log_format))
    
            logging.getLogger('').addHandler(console)

        ret = logging.getLogger('pyser')

        return ret

    @staticmethod
    def get_logger():
        if not _Logger._logger:
            if _Logger.verbose:
                _Logger._logger = _Logger._setup_logger()
            else:
                _Logger._logger = _LoggerMockup()

        return _Logger._logger

    @staticmethod
    def reset_logger():
        _Logger._logger = None
        _Logger.get_logger()


__indents = []


def indent_push():
    global __indents, _INDENT
    __indents.append( _INDENT)


def indent_pop():
    global __indents, _INDENT
    if __indents:
        _INDENT = __indents.pop(-1)


def indent():
    global _INDENT, _INDENT_STEP
    _INDENT += ' ' * _INDENT_STEP
    return _Logger.get_logger()


def unindent():
    global _INDENT, _INDENT_STEP
    if len(_INDENT) >= _INDENT_STEP:
        _INDENT = _INDENT[:-_INDENT_STEP]
    return _Logger.get_logger()


def get_indent_size():
    return len(_INDENT)


def __log(logger_function, message, flag=0):
    if _Logger.verbose & flag:
        logger_function(_INDENT + str(message))
    return _Logger.get_logger()


def set_verbosity(verbose):
    if _Logger.verbose == verbose:
        return

    was_verbose = _Logger.verbose

    _Logger.verbose = verbose
    
    if not was_verbose:
        _Logger.reset_logger()


def info(message):
    return __log(_Logger.get_logger().info, message, Verbosity.INFO)


def debug(message):
    return __log(_Logger.get_logger().debug, message, Verbosity.DEBUG)


def warning(message):
    return __log(_Logger.get_logger().warning, message, Verbosity.WARNING)


def error(message):
    return __log(_Logger.get_logger().error, message, Verbosity.ERROR)


def blank():
    return __log(_Logger.get_logger().info, '')


if __name__ == '__main__':
    pass