#!/usr/bin/env python
# coding=utf-8

import re
import logger
from utils import pyser_assert
from lexer import Token
from parser import Node, SelectNode
from rules import Identifier, Command, Bracket, Operator, Function, Numeric
from operations import *
from decorators import footprint
from exceptions import InterpreterError, InternalError

RE_FLAGS = re.S | re.MULTILINE


@footprint
def _distinct(data):
    """Get set of unique elements.

    Args:
        data: A list of elements.

    Returns:
        List of unique elements.
    """

    if isinstance(data, list):
        return list(set(data))
    else:
        return data


@footprint
def _distinct_each(data):
    result = []

    for element in data:
        if isinstance(element, list):
            result.append(_distinct(element))
        elif isinstance(element, str):
            new_str = ''
            for char in element:
                if char not in new_str:
                    new_str += char
            result.append(new_str)

    return result


@footprint
def __rpn(commands):

    stack = []
    out = []

    for c in commands:
        if c.type is Bracket.LEFT:
            stack.append(c)
        elif c.type is Bracket.RIGHT:
            while stack[-1].type is not Bracket.LEFT:
                out.append(stack.pop(-1))
            stack.pop(-1)
        elif c.type in Operator.members():
            if not len(stack):
                stack.append(c)
            elif c.type.priority > stack[-1].type.priority:
                stack.append(c)
            else:
                while stack[-1].type.priority > c.type.priority:
                    out.append(stack.pop(-1))
                    if not len(stack):
                        break
                stack.append(c)
        else:
            out.append(c)

    out += stack[::-1]

    return out


@footprint
def __calc_operator(a, b, operator):
    a, b = int(a), int(b)

    if operator is Operator.ADD:
        return a + b
    elif operator is Operator.SUB:
        return a - b
    elif operator is Operator.MUL:
        return a * b
    elif operator is Operator.DIV:
        return a // b
    elif operator is Operator.MOD:
        return a % b
    elif operator is Operator.POW:
        return a ** b
    else:
        raise InterpreterError('Unknown operator: %s' % operator)


@footprint
def __get_args(fstring):

    fstring = fstring.strip()
    logger.debug(fstring)
    fstring = fstring[:-1]
    logger.debug(fstring)
    fstring = fstring.split('(')[1]

    fargs = []
    for x in fstring.split(','):
        x = x.strip()

        try:
            int(x)
        except ValueError:
            x = Token(x, Identifier.ID)
        else:
            x = Token(x, Numeric.INT)

        fargs.append(x)

    return fargs


@footprint
def __get_value(value, result=None):
    pyser_assert(isinstance(result, Result), InternalError('#1'))
    if isinstance(value, (int, long)):
        return value
    if isinstance(value, Token):
        if value.type is Numeric.INT:
            return int(value.token)

        pyser_assert(isinstance(result, Result), InternalError('#1'))

        if value.type is Identifier.ID:
            try:
                return result.named_groups[value.token][0]
            except IndexError:
                return result.named_groups[value.token]
        elif value.type is Function.MAX:
            return pyser_fmax(__get_args(value.token), result)
        elif value.type is Function.MIN:
            return pyser_fmin(__get_args(value.token), result)
        elif value.type is Function.REPLACE:
            return pyser_freplace(__get_args(value.token), result)
        elif value.type is Function.SUM:
            return pyser_fsum(__get_args(value.token), result)
        elif value.type is Function.COUNT:
            return pyser_fcount(__get_args(value.token), result)
        elif value.type is Command.SUM:
            return pyser_sum(result.get_values())
        elif value.type is Command.MIN:
            return pyser_min(result.get_values())
        elif value.type is Command.MAX:
            return pyser_max(result.get_values())
        elif value.type is Command.COUNT:
            return pyser_count(result.get_values())
        else:
            raise InternalError('Unsupported token: %s' % value)

    raise InternalError('Unknown type of %s: %s' % (value, type(value)))


@footprint
def __calc_rpn(commands, result):
    logger.debug('calc_rpn')
    logger.debug('command=%s' % [type(x) for x in commands])
    logger.debug('result=%s' % result)
    stack = []

    for c in commands:
        if c.type in Operator.members():
            pyser_assert(len(stack) >= 2, InterpreterError('Insufficient number of arguments for operator %s' % c))

            b, a = stack.pop(-1), stack.pop(-1)

            logger.debug('type(a)=%s' % type(a))
            logger.debug('named=%s' % result.named_groups)

            stack.append(__calc_operator(a, b, c.type))
        else:
            logger.debug('append stack: %s is %s = %s' % (c, c.type, c.token))
            stack.append(__get_value(c, result))

    logger.debug('stack=%s' % stack)

    return stack[0]


@footprint
def __backward_mode(commands, result):
    found = result.get_values()

    for c in commands:
        logger.debug('pre-found: %s' % found)
        logger.debug('%s: %s,%s' % (c, c.type, c.token))

        pyser_assert(c.type in Command.members() or c.type in Function.members() or
                    c.type in Identifier.members() or c.type in Numeric.members(),
                    InterpreterError('Does not compute: %s' % c))

        if c.type is Command.MIN:
            found = [pyser_min(found)]
        elif c.type is Command.MIN_EACH:
            found = pyser_min_each(Result(found=found)).get_values()
        elif c.type is Command.MAX:
            found = [pyser_max(found)]
        elif c.type is Command.MAX_EACH:
            found = pyser_max_each(Result(found=found)).get_values()
        elif c.type is Command.SUM:
            found = [pyser_sum(found)]
        elif c.type is Command.COUNT:
            found = [pyser_count(found)]
        elif c.type is Command.COUNT_EACH:
            found = pyser_count_each(found)
        elif c.type is Function.REPLACE:
            found = pyser_freplace(__get_args(c.token), result)
        elif c.type is Function.MAX:
            found = [pyser_fmax(__get_args(c.token), result)]
        elif c.type is Function.MIN:
            found = [pyser_fmin(__get_args(c.token), result)]
        elif c.type is Function.SUM:
            found = [pyser_fsum(__get_args(c.token), result)]
        elif c.type is Command.DISTINCT:
            found = pyser_distinct(found)
        elif c.type is Command.DISTINCT_EACH:
            found = pyser_distinct_each(found)
        elif c.type is Numeric.INT:
            pyser_assert(len(commands) == 1, InterpreterError('The syntax makes no sense: %s' % commands))
            found = [int(c.token)]
        elif c.type is Identifier.ID:
            pyser_assert(len(commands) == 1, InterpreterError('The syntax makes no sense: %s' % commands))
            found = [__get_value(c, result)]
        else:
            raise NotImplementedError(c)

    return found


@footprint
def run(result, node):

    if result is None:
        result = Result()
    elif isinstance(result, basestring):
        result = Result(data=result)

    pyser_assert(isinstance(node, Node),
                InterpreterError('Expected a Node instance: %s' % type(node)))
    pyser_assert(isinstance(result, Result),
                InterpreterError('Expected a Result instance: %s' % result))

    if node.nested:
        result = run(result, node.source)

    result_grouping = node.group is not None

    logger.debug('result=%s' % result)

    for select_node in node.parts:
        # Assert: identifiers or grouping
        if result_grouping:
            pyser_assert(not select_node.identifier,
                        InterpreterError('Groups and identifiers combined...'))

        # Assert: use an identifier not present in the results
        for command in select_node.commands:
            pyser_assert(command.type is not Identifier.ID or command.token in result.named_groups.keys(),
                        InterpreterError('Unknown identifier: %s (ids: %s, commands: %s)'
                                         % (command.token, result.named_groups.keys(), select_node.commands)))

    partial_results = []

    for select_node in node.parts:
        logger.debug('process: %s' % select_node)
        logger.debug('filter=%s' % select_node.filter_)

        if select_node.filter_:
            new_result = result.get_filtered(select_node.filter_)
        else:
            new_result = Result(result=result)

        logger.debug('result_grouping=%s' % result_grouping)

        if result_grouping:
            groups = {}
            for value in new_result.get_values():
                value = str(value)

                f = re.findall(node.group.token[1:-1], value)

                if not f:
                    key = ''
                else:
                    key = f[0]

                if key not in groups:
                    groups[key] = []

                groups[key].append(value)

            new_result.reset()
            new_result.anon_groups = groups

        assert isinstance(select_node, SelectNode)

        if select_node.commands:
            if select_node.operators:
                rpn = __rpn(select_node.commands)
                logger.debug('rpn=%s' % rpn)
                select_node_result = __calc_rpn(rpn, new_result)
            else:
                rpn = sorted(select_node.commands, key=lambda x: x.type.priority)[::-1]
                select_node_result = __backward_mode(rpn, new_result)

            if not isinstance(select_node_result, list):
                select_node_result = [select_node_result]

            if select_node.identifier:
                logger.debug('ID: named[%s] = %s' % (select_node.identifier.token, select_node_result))
                new_result.reset()
                new_result.named_groups[select_node.identifier.token] = select_node_result
            else:
                logger.debug('Anon: found += %s' % select_node_result)
                logger.debug('pre=%s' % new_result)
                new_result.reset()
                logger.debug('post=%s' % new_result)
                new_result.found.extend(select_node_result)
                logger.debug('final=%s' % new_result)
        else:
            if select_node.identifier:
                f = new_result.found
                new_result.reset()
                new_result.named_groups[select_node.identifier.token] = f

        partial_results.append(new_result)

    new_result = Result.merge(*partial_results)

    # Result post-processing
    for index, processor in enumerate(node.post_processors):
        logger.debug('processor=%s' % processor)

        if processor.type is Command.LIMIT:
            limit_arg = node.post_processors[index+1]

            pyser_assert(isinstance(limit_arg, Token),
                        InterpreterError.bad_arg('limit', limit_arg.token, 'number'))
            pyser_assert(limit_arg.type is Numeric.INT,
                        InterpreterError.bad_arg('limit', limit_arg.token, 'number'))

            new_result.limit(int(limit_arg.token))

    return new_result

if __name__ == '__main__':
    pass
