#!/usr/bin/env python
# coding=utf-8

import re
import logger
from utils import pyser_assert
from exceptions import RulesError

# Function's arguments pattern
_FUNCTION_ARGS_PATTERN = r'\([,\s\dA-Z]+\)'


class _RulesContainer(object):

    _MEMBERS = None

    @classmethod
    def members(cls):
        if not cls._MEMBERS:
            cls._MEMBERS = [getattr(cls, x) for x in dir(cls) if x.isupper() and not x.startswith('_')]
        return cls._MEMBERS


class TokenType(object):
    """ Type of token.
    """

    def __init__(self, name, pattern=None, priority=0):
        """ Initialize TokenType with name, pattern and priority.

        :param name: Type name.
        :param pattern: Regular expression describing type's syntax.
        :type pattern: str
        :param priority: Priority used to determine order when multiple commands are computed.
        :type priority: int
        """

        if pattern is None:
            pattern = r'%s$' % name.upper()

        pyser_assert(isinstance(name, basestring), RulesError('Incorrect token name: %s' % name))
        pyser_assert(isinstance(pattern, basestring), RulesError('Incorrect token pattern: %s' % pattern))

        self.name = name
        self.pattern = re.compile(pattern)
        self.priority = priority

    def __repr__(self):
        return self.name


class Command(_RulesContainer):
    """ Pyser commands.
    """

    SELECT = TokenType('select')
    AS = TokenType('as')
    SUM = TokenType('sum', priority=2)
    SUM_EACH = TokenType('sum each', priority=2)
    FROM = TokenType('from')
    GROUP = TokenType('group by')
    ORDER = TokenType('order by')
    MIN = TokenType('min', priority=1)
    MIN_EACH = TokenType('min each', priority=1)
    MAX = TokenType('max', priority=1)
    MAX_EACH = TokenType('max each', priority=1)
    ORDER_ASC = TokenType('order asc')
    ORDER_DESC = TokenType('order desc')
    COUNT = TokenType('count', priority=3)
    COUNT_EACH = TokenType('count each', priority=3)
    DISTINCT = TokenType('distinct', priority=4)
    DISTINCT_EACH = TokenType('distinct each', priority=4)
    LIMIT = TokenType('limit')


class Function(_RulesContainer):
    """ Pyser functions.
    """

    REPLACE = TokenType('replace()', r'(REPLACE|REPL)%s$' % _FUNCTION_ARGS_PATTERN, 10)
    SUM = TokenType('sum()', r'SUM%s$' % _FUNCTION_ARGS_PATTERN, 3)
    MIN = TokenType('min()', r'MIN%s$' % _FUNCTION_ARGS_PATTERN, 1)
    MAX = TokenType('max()', r'MAX%s$' % _FUNCTION_ARGS_PATTERN, 1)
    COUNT = TokenType('count()', r'COUNT%s$' % _FUNCTION_ARGS_PATTERN, 2)


class Bracket(_RulesContainer):
    """ Brackets.
    """

    LEFT = TokenType('(', r'\($')
    RIGHT = TokenType(')', r'\)$')


class Operator(_RulesContainer):
    """ Arithmetic operators.
    """

    POW = TokenType('**', '(\*\*|\^)$', 4)
    MUL = TokenType('*', '\*$', 3)
    DIV = TokenType('/', '/$', 3)
    MOD = TokenType('%', '%$', 2)
    ADD = TokenType('+', '\+$', 1)
    SUB = TokenType('-', '-$', 1)


class Separator(_RulesContainer):
    """ Syntax separators.
    """

    COMMA = TokenType('comma', r',$')


class Identifier(_RulesContainer):

    ID = TokenType('identifier', r'[A-Z]+[_A-Z0-9]*$')


class RegularExpression(_RulesContainer):

    RE = TokenType('re', r'\'.*\'$')


class Numeric(_RulesContainer):
    """Numeric types.
    """

    INT = TokenType('number', '\d+$')


class Type(_RulesContainer):
    """Pyser types taxonomy.
    """

    RE = RegularExpression
    NUMERIC = Numeric
    COMMAND = Command
    BRACKET = Bracket
    FUNCTION = Function
    IDENTIFIER = Identifier
    OPERATOR = Operator
    SEPARATOR = Separator


def find_type(token):
    """Check if given piece of code matches any definition rule.

    :param token: Code to be checked.
    :type token: str
    :return Rule definition name if found, None otherwise.
    """

    token = token.upper()

    for type_ in Type.members():
        for subtype in type_.members():
            if subtype.pattern.match(token):
                logger.debug('found: %s -> %s' % (token, subtype))
                return subtype

    return None