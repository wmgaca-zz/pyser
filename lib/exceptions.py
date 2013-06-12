#!/usr/bin/env python
# coding=utf-8


class _PyserBaseError(Exception):
    """Base for all Pyser exceptions.
    """

    def __str__(self):
        return '%s: %s' % (self.__class__.__name__, super(_PyserBaseError, self).__str__())


class RulesError(_PyserBaseError):
    """Thrown on rules errors.
    """

    pass


class LexerError(_PyserBaseError):
    """Thrown on Pyser lexer errors.
    """

    pass


class ParserError(_PyserBaseError):
    """Thrown on Pyser parser errors.
    """

    @staticmethod
    def bad_arg(command, value, correct_type):
        return ParserError('Incorrect %s argument: %s (required: %s)'
                           % (command.upper(), value.upper(), correct_type.upper()))

    @staticmethod
    def grammar(index, tokens):
        return ParserError('Incorrect grammar at %s in %s' % (index, tokens))

    @staticmethod
    def unbalanced(index, tokens):
        return ParserError('Unbalanced parentheses at %s in %s' % (index, tokens))

    @staticmethod
    def repeated(what, index, token):
        return ParserError('Repeated %s at %s in %s' % (what.upper(), index, token))


class InterpreterError(_PyserBaseError):
    """Thrown on Pyser interpreter errors.
    """

    @staticmethod
    def bad_arg(command, value, correct_type):
        return ParserError('Incorrect %s argument: %s (required: %s)'
                           % (command.upper(), value.upper(), correct_type.upper()))


class InternalError(_PyserBaseError):
    """Internal errors that should-never-happen.
    """

    pass