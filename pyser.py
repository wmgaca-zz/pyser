#!/usr/bin/env python
# coding=utf-8

from HTMLParser import HTMLParser
from lib import logger, lexer, parser, interpreter
from lib.parser import Node
from lib.exceptions import LexerError
from lib.rules import Type
from lib.utils import pyser_assert
from lib.decorators import footprint


@footprint
def get_file_contents(path):
    try:
        return open(path).read()
    except IOError:
        print 'Given file does not exist: %s' % path
        return None


@footprint
def print_usage_and_exit(error_msg=None):
    if error_msg:
        print '\n    Error: %s' % error_msg

    usage = '''
    Usage:
        python pyser.py -d data_file -c code_file [ -D ] [ -t ]

        -d, --data        Data file path
        -c, --code        Code file path
        -D  --debug       Turn debug mode on (debug info visible)
        -t  --run-tests   Run unit tests'''

    print(usage)

    exit()


@footprint
def run(file_path, code, debug=False):

    if debug:
        logger.set_verbosity(logger.Verbosity.ALL)

    if file_path:
        data = get_file_contents(file_path)
    else:
        data = None

    code = HTMLParser().unescape(code)

    logger.debug('Input:\n%s' % data)

    logger.debug('Code:\n\t\t\t%s\n' % code)
    
    tokens = lexer.parse(code) 

    logger.debug('Lexer output:')
    for i, t in enumerate(tokens):
        logger.debug('\t%d: %s' % (i, t))
    logger.debug('')

    pyser_assert(tokens[0].type is Type.COMMAND.SELECT,
                LexerError('Incorrect type of first token: %s' % tokens[0]))

    node = parser.build_tree(tokens)

    assert isinstance(node, Node)

    logger.debug('Parser output:\n\n%s' % node)

    result = interpreter.run(result=data, node=node)

    return result.get_values()