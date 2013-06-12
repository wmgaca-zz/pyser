#!/usr/bin/env python
# coding=utf-8

import time
from exceptions import _PyserBaseError

ERROR_VALUE = -1


def get_timestamp():
    """Returns timestamp for logger and file naming usage.
    """

    return time.strftime('%Y%m%d_%H%M%S')


def pyser_assert(condition, exception=_PyserBaseError):
    """Custom assert.

    :param condition: Assertion condition
    :type condition: bool
    :param exception: Exception to be thrown (exception instance)
    :type exception: _PyserBaseError
    """

    if not condition: 
        raise exception


def get_types(token_list):
    return list(set([token.type for token in token_list]))


def type_in(token_type, token_list):
    return token_type in get_types(token_list)


def types_in(token_types, token_list):
    return len(set(token_types) & set(get_types(token_list))) > 0