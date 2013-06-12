#!/usr/bin/env python
# coding=utf-8

import re
import logger
from utils import pyser_assert
from rules import RegularExpression, TokenType, find_type
from decorators import footprint
from exceptions import RulesError, LexerError


class Token(object):

    def __init__(self, token, token_type):
        pyser_assert(isinstance(token, basestring),
                    RulesError('Incorrect token: %s' % token))
        pyser_assert(isinstance(token_type, TokenType),
                    RulesError('Incorrect token type: %s' % type(token_type)))

        self.token = token
        self.type = token_type

    def __repr__(self):
        return self.token


@footprint
def __tokenize_non_re(code):
    """Convert query code to tokens (except regular expressions).

    Function tries to match the given code to language's tokens. The token search is greedy.

    :param code: Pyser code string.
    :type code: str
    :return: List of tokens.
    """

    code = code.strip()
    result, end = [], len(code) - 1

    pyser_assert(len(code) > 0, LexerError('Node code to tokenize: %s' % code))

    while len(code):
        pyser_assert(end >= 0, LexerError('Cannot tokenize value: %s' % code))

        current = code[:end+1].strip()

        token_type = find_type(current)

        if token_type:
            code = code[end+1:]
            end = len(code) - 1
            logger.debug('Token(%s, %s)' % (current, token_type))
            result.append(Token(current, token_type))
        else:
            end -= 1

    pyser_assert(len(result) > 0, LexerError('Failed to tokenize the code.'))

    logger.debug('result=%s' % result)

    return result


@footprint
def __tokenize(code):
    """Convert query code to tokens.

    Function extracts all regular expressions and calls __tokenize_non_re to lex the rest.

    :param code: Pyser code string
    :type code: str
    :return: List of tokens.
    """

    if not code:
        return []

    escaped, start = False, None

    for i, char in enumerate(code):
        if escaped:
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == "'":
            if not start:
                start = i
            else:
                pre = __tokenize_non_re(code[:start])
                regexp = Token(code[start:i+1].strip(), RegularExpression.RE)
                post = __tokenize(code[i+1:])

                return pre + [regexp] + post

    return __tokenize_non_re(code)


@footprint
def parse(code):
    """Parse Pyser query code to tokens.

    :param code: Pyser code string.
    :type code: str
    :return: List of tokens.
    """

    code = re.sub(r'\n', ' ', code)

    pyser_assert(len(code) > 0, LexerError('Empty code string: %s' % code))

    tokens = __tokenize(code)

    pyser_assert(len(tokens) > 0, LexerError('No tokens found: %s' % code))

    return tokens