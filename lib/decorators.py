#!/usr/bin/env python
# coding=utf-8

import re
import inspect
import logger as logging

# key: function, value: boolean -- has return statement?
_has_return_statement = {}


def __function_has_return_statement(function):
    """ Helper function, checks if a function given as a parameter
        has a return statement. Returns boolean."""

    if function not in _has_return_statement:
        pattern = re.compile(r'(^| |:)return($| |\()')
        found = [x for x in inspect.getsource(function).split('\n') if pattern.findall(x)]
        _has_return_statement[function] = len(found) > 0

    return _has_return_statement[function]


def __get_function_parameters(function, *args, **kwargs):
    """ Helper function, returns a dictionary containing function
        parameter names and values."""

    # Get names and default arguments
    fargspec = inspect.getargspec(function)

    if fargspec.defaults:
        arglist = dict([(name, default)
                        for name, default
                        in zip(fargspec.args, fargspec.defaults)])
    else:
        arglist = dict([(name, None) for name in fargspec.args])

    # Get argument values passed to the function
    unnamed = []
    if args:
        for i, value in enumerate(args):
            try:
                arglist[fargspec.args[i]] = value
            except IndexError:
                unnamed.append(value)
    if kwargs:
        for name, value in kwargs.items():
            arglist[name] = value

    # Create final list of all arguments and their values
    farglist = []
    for name, value in arglist.items():
        farglist.append((name, value,))
    for value in unnamed:
        farglist.append(('?', value,))

    return farglist


def __format_value(value):
    if isinstance(value, basestring):
        value = re.sub(r'\r\n', ' ', value)
        value = re.sub(r'\n', ' ', value)
        value = "'%s'" % value

    return value


def __format_arg(name, value):
    return '%s = %s' % (name, __format_value(value))

def footprint(function):

    # Make sure that passed argument is a function
    assert inspect.isfunction(function), 'Cannot decorate: not a function!'

    def function_wrapper(*args, **kwargs):
        # Get function arguments and their values
        farglist = __get_function_parameters(function, *args, **kwargs)

        # Print the header: what function was called
        # and what argument values were passed
        call_str = 'CALL %s.%s (' % (function.__module__, function.__name__)

        if not farglist:
            logging.debug('%s)' % call_str)
        elif len(farglist) == 1:
            logging.debug('%s%s)' % (call_str, __format_arg(*farglist[0])))
        else:
            indent = ' ' * len(call_str)

            # First parameter
            logging.debug('%s%s' % (call_str, __format_arg(*farglist[0])))

            # [1:-1] parameters
            for name, value in farglist[1:-1]:
                logging.debug('%s%s' % (indent, __format_arg(name, value)))

            # Last parameters
            logging.debug('%s%s)' % (indent, __format_arg(*farglist[-1])))

        logging.indent()

        # Invoke the functions
        result = function(*args, **kwargs)

        # Print footer and the return value (if present)
        if __function_has_return_statement(function):
            logging.debug('END  %s -> %s' % (function.__name__,
                                             __format_value(result)))
        else:
            logging.debug('END  %s' % function.__name__)

        logging.unindent()

        # Return function result
        return result

    return function_wrapper


def assert_not_none(function):
    def function_wrapper(*args, **kwargs):
        result = function(*args, **kwargs)
        assert result is not None, 'Function %s output is None!' % function.__name__
        return result
    return function_wrapper


# Auto decoration

DO_NOT_DECORATE_FLAG = '__do_not_decorate'


def disable_auto_decoration(function):
    setattr(function, DO_NOT_DECORATE_FLAG, True)
    return function


def auto_decoration_enabled(function):
    return inspect.isfunction(function) and not hasattr(function, DO_NOT_DECORATE_FLAG)


class _DecorateAllMethods(type):

    _decorator_name = None
    _disable = []

    def __new__(mcs, name, bases, local):
        assert mcs._decorator_name in globals()

        decorator = globals()[mcs._decorator_name]

        assert callable(decorator), 'Something went terribly wrong.'

        for attr_name, attr_value in local.items():
            if attr_name in mcs._disable:
                continue
            if not auto_decoration_enabled(attr_value):
                continue

            local[attr_name] = decorator(attr_value)

        return super(_DecorateAllMethods, mcs).__new__(mcs, name, bases, local)


class FootprintAllMethods(_DecorateAllMethods):

    _decorator_name = 'footprint'
    _disable = ['__repr__', '__str__']
