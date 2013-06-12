#!/usr/bin/env python
# coding=utf-8

import re
import copy
import logger
from utils import ERROR_VALUE, pyser_assert
from decorators import FootprintAllMethods, disable_auto_decoration, footprint
from exceptions import InterpreterError, InternalError

RE_FLAGS = re.S | re.MULTILINE


class Result(object):

    __metaclass__ = FootprintAllMethods

    @disable_auto_decoration
    def __init__(self, result=None, named_groups=None, anon_groups=None, found=None, data=None):
        self.data = None
        self.named_groups = {}
        self.anon_groups = {}
        self.found = []

        if result:
            self.data = result.data
            self.named_groups = copy.deepcopy(result.named_groups)
            self.anon_groups = copy.deepcopy(result.anon_groups)
            self.found = copy.deepcopy(result.found)

        if named_groups:
            self.named_groups = named_groups
        if anon_groups:
            self.anon_groups = anon_groups
        if found:
            self.found = found
        if data:
            self.data = data

    @disable_auto_decoration
    def __str__(self):
        return ('named: %s, anon: %s, found: %s'
                % (self.named_groups, self.anon_groups, self.found))

    def get_values(self):
        values = []

        for val in self.anon_groups.values():
            values += val

        for val in self.named_groups.values():
            values += val

        values += self.found

        if self.data:
            values += [self.data]

        return values

    def get_filtered(self, filter_):
        result = Result()

        result.found = pyser_filter(filter_, self.get_values())

        return result

    def reset(self):
        self.__init__()

    def limit(self, n):
        self.found = self.found[:n]

        for key, value in self.named_groups:
            self.named_groups[key] = value[:n]

        for key, value in self.anon_groups:
            self.anon_groups[key] = value[:n]

    @staticmethod
    @disable_auto_decoration
    def merge(*results):
        result = Result()

        for r in results:
            pyser_assert(isinstance(r, Result), InterpreterError("Incorrect argument type: %s" % r))

            result.found.extend(r.found)

            # No collisions allowed
            for k, v in r.named_groups.items():
                pyser_assert(k not in result.named_groups)
                result.named_groups[k] = v

            # Merge collisions
            for k, v in r.anon_groups.items():
                if k in result.anon_groups:
                    result.anon_groups[k].extend(v)
                else:
                    result.anon_groups[k] = v

        return result


@footprint
def pyser_max(values):
    if not values:
        return ERROR_VALUE

    return unify(values, sort=True)[-1]


@footprint
def pyser_min(values):
    if not values:
        return ERROR_VALUE

    return unify(values, sort=True)[0]


@footprint
def pyser_sum(values):
    if not values:
        return 0

    return reduce(lambda x, y: x + y, unify(values))


@footprint
def pyser_count(values):
    return len(values)


@footprint
def pyser_count_each(values):
    return [len(str(x)) for x in values]


@footprint
def pyser_fmax(args, result):
    values = []

    for arg in args:
        try:
            value = int(arg.token)
        except ValueError:
            pyser_assert(arg.token in result.named_groups, InterpreterError('Unknown identifier'))
            values += result.named_groups[arg.token]
        else:
            values.append(value)

    return pyser_max(values)


@footprint
def pyser_fmin(args, result):
    values = []

    for arg in args:
        try:
            value = int(arg.token)
        except ValueError:
            pyser_assert(arg.token in result.named_groups, InterpreterError('Unknown identifier'))
            values += result.named_groups[arg.token]
        else:
            values.append(value)

    return pyser_min(values)


@footprint
def pyser_fsum(args, result):
    values = []

    for arg in args:
        try:
            value = int(arg.token)
        except ValueError:
            pyser_assert(arg.token in result.named_groups, InterpreterError('Unknown identifier'))
            values += result.named_groups[arg.token]
        else:
            values.append(value)

    return pyser_sum(values)


@footprint
def pyser_fcount(args, result):
    values = []

    for arg in args:
        try:
            value = int(arg.token)
        except ValueError:
            pyser_assert(arg.token in result.named_groups, InterpreterError('Unknown identifier'))
            values += result.named_groups[arg.token]
        else:
            values.append(value)

    return pyser_count(values)


@footprint
def pyser_freplace(args, result):
    pyser_assert(len(args) == 2, InterpreterError('Incorrect REPLACE arguments: %s' % args))

    replace_from, replace_to = tuple([str(x) for x in args])

    if isinstance(result, Result):
        return [replace_to if str(x) == replace_from else x for x in result.get_values()]
    elif isinstance(result, list):
        return [replace_to if str(x) == replace_from else x for x in result]
    else:
        raise NotImplementedError


@footprint
def pyser_distinct(values):
    return list(set(values))


@footprint
def pyser_distinct_each(values):
    result = []

    for element in values:
        if isinstance(element, list):
            result.append(pyser_distinct_each(element))
        elif isinstance(element, (basestring, int)):
            new = ''
            for char in str(element):
                if char not in new:
                    new += char
            result.append(new)

    return result


@footprint
def pyser_min_each(input_):
    assert isinstance(input_, Result)

    result = Result()

    if input_.found:
        result.found = [pyser_min(input_.found)]

    for key, value in input_.named_groups.items():
        if not value:
            continue
        result.named_groups[key] = [pyser_min(value)]

    for key, value in input_.anon_groups.items():
        if not value:
            continue
        result.anon_groups[key] = [pyser_min(value)]

    return result


@footprint
def pyser_max_each(result):
    new_result = Result()

    if result.found:
        new_result.found = [pyser_max(result.found)]

    for key, value in result.named_groups.items():
        if not value:
            continue
        new_result.named_groups[key] = [pyser_max(value)]

    for key, value in result.anon_groups.items():
        if not value:
            continue
        new_result.anon_groups[key] = [pyser_max(value)]

    return new_result


@footprint
def unify(values, sort=False):
    result = []
    for x in values:
        try:
            result.append(int(x))
        except ValueError:
            result = [str(x) for x in values]
            break

    if sort:
        result.sort()

    return result


@footprint
def pyser_filter(filter_, data):
    if isinstance(data, list):
        found = []
        for elem in data:
            found += pyser_filter(filter_, elem)
        return found
    elif isinstance(data, basestring):
        logger.debug('filter=%s (%s)' % (filter_, type(filter_)))
        return re.findall(filter_, data, RE_FLAGS)
    else:
        raise InternalError('Unsupported data type: %s' % data)