#!/usr/bin/env python
# coding=utf-8

from rules import *
from decorators import footprint
from utils import pyser_assert, get_types, type_in, types_in
from exceptions import ParserError
import logger


class Node(object):

    def __init__(self):
        self.__source = None
        self.group = None
        self.parts = []
        self.post_processors = []

    @property
    def source(self):
        return self.__source

    @source.setter
    def source(self, value):
        pyser_assert(self.__source is None, ParserError('Multiple source in %s' % self))
        self.__source = value

    @property
    def nested(self):
        return isinstance(self.source, Node)

    @property
    def multiple(self):
        return len(self.parts) > 1

    def to_string(self, indent_sz=4):
        indent = ' ' * indent_sz
        string = ''

        # noinspection PyArgumentList
        for index, part in enumerate(self.parts, start=1):
            string += '%s#%s: %s (operators: %s)\n' % (indent, index, part, part.operators)

        if self.nested:
            string += '%sfrom (\n%s%s)\n' % (indent, self.source.to_string(indent_sz + 4), indent)
        else:
            string += '%sfrom: %s\n' % (indent, self.source)

        string += '%spost: %s\n' % (indent, self.post_processors)

        return string

    def __str__(self):
        return '[NODE] parts: %s, from: %s, post: %s' % (self.parts, self.source, self.post_processors)


class SelectNode(object):

    def __init__(self):
        self.filter_ = None
        self.commands = []
        self.identifier = None

    @property
    def types(self):
        """Distinct token type list.
        """
        return get_types(self.commands)

    @property
    def operators(self):
        """Intersection.
        """
        return types_in(Operator.members(), self.commands)

    def __str__(self):
        return '%s: %s, %s' % (self.identifier, self.filter_, self.commands)

    __repr__ = __str__


@footprint
def build_tree(tokens):
    """Create a parse tree from token list.

    :param tokens: List of tokens.
    :type tokens: list
    :return: Parse tree root node.
    """

    node = Node()
    i = 0

    while i < len(tokens):
        token = tokens[i]

        # First token on the list or a comma separator
        if i == 0 or token.type is Separator.COMMA:
            node.parts.append(SelectNode())

        # FROM
        elif token.type is Command.FROM:
            pyser_assert(node.source is None,
                         ParserError('Multiple source at %s in %s' % (i, tokens)))

            next_token = tokens[i+1]
            pyser_assert(next_token.type is Bracket.LEFT,
                         ParserError.grammar(i, tokens))

            bracket_count = 1
            end = i+3

            while True:
                if 0 == bracket_count:
                    break

                pyser_assert(end != len(tokens),
                             ParserError.unbalanced(i+1, tokens))

                if tokens[end].type is Bracket.LEFT:
                    bracket_count += 1
                elif tokens[end].type is Bracket.RIGHT:
                    bracket_count -= 1
                end += 1
            end -= 1

            logger.debug('Recursion at %s-%s' % (i+1, end))

            node.source = build_tree(tokens[i+2:end])

            i = end

        # <RE>
        elif token.type is RegularExpression.RE:
            pyser_assert(node.parts[-1].filter_ is None,
                         ParserError.repeated('filter', i, tokens))

            node.parts[-1].filter_ = token.token[1:-1]

        # AS <ID>
        elif token.type is Command.AS:
            pyser_assert(node.parts[-1].identifier is None,
                         ParserError.repeated('identifier', i, tokens))

            i += 1
            next_token = tokens[i]

            pyser_assert(next_token.type is Identifier.ID,
                         ParserError.grammar(i, tokens))

            node.parts[-1].identifier = next_token

        # ORDER ASC, ORDER DESC, ORDER <RE>
        elif token.type in [Command.ORDER_ASC, Command.ORDER_DESC, Command.ORDER]:
            pyser_assert(not types_in([Command.ORDER, Command.ORDER_ASC, Command.ORDER_DESC], node.post_processors),
                         ParserError.repeated('order', i, tokens))

            node.post_processors.append(token)

            if token.type is Command.ORDER:
                i += 1
                next_token = tokens[i]

                pyser_assert(next_token.type is RegularExpression.RE,
                             ParserError.grammar(i, tokens))

                node.post_processors.append(next_token)

        # LIMIT <INT>
        elif token.type in [Command.LIMIT]:
            pyser_assert(not type_in(Command.LIMIT, node.post_processors),
                         ParserError.repeated('limit', i, tokens))

            node.post_processors.append(token)

            i += 1
            next_token = tokens[i]

            pyser_assert(next_token.type is Numeric.INT,
                         ParserError.grammar(i, tokens))

            node.post_processors.append(next_token)

        # GROUP BY <RE>
        elif token.type is Command.GROUP:
            #pyser_assert(not type_in(Command.GROUP, node.post_processors),
            #             ParserError.repeated('group', i, tokens))

            #node.post_processors.append(token)

            i += 1
            next_token = tokens[i]

            pyser_assert(next_token.type is RegularExpression.RE,
                         ParserError.grammar(i, tokens))

            #node.post_processors.append(next_token)
            node.group = next_token

        # SUM, MIN, MAX, COUNT, FUNCTION()
        else:
            logger.debug('append %s -> %s' % (i, token))
            node.parts[-1].commands.append(token)

        i += 1

    logger.debug('parts: %s' % node.parts)

    return node