#!/usr/bin/env python
# coding=utf-8

import unittest
import os
from xml.dom import minidom
import pyser
from lib import logger, lexer, parser
from lib.exceptions import LexerError, ParserError, InterpreterError


class Test(object):

    def __init__(self, code, result=None, file_path=None):
        self.code = code
        self.result = result
        self.file_path = file_path

    def run(self):
        result = pyser.run(file_path=self.file_path,
                          code=self.code,
                          debug=False)
        return int(result[0])


class TestCase(unittest.TestCase):

    _verbosity = logger.Verbosity.INFO

    def setUp(self):
        logger.set_verbosity(self._verbosity)
        logger.info('Running %s' % self)
        logger.indent()

    def tearDown(self):
        logger.unindent()
        logger.info('')


class LexerTest(TestCase):

    def run_tests(self, tests):
        for test in tests:
            tokens = lexer.parse(test)
            logger.info('Pyser Query: %s -> %s' % (test.replace('\n', ' '), tokens))
            for token in tokens:
                self.assert_(isinstance(token, lexer.Token))

    def run_tests_negative(self, tests):
        for test in tests:
            logger.info('Pyser Query: %s' % test.strip())
            logger.indent_push()
            self.assertRaises(LexerError, lexer.parse, test)
            logger.indent_pop()

    def test_lexer(self):
        tests = ["SELECT 1 + 1 * 1 (2+2)/3%5**2^5*(5/5)",
                 "SELECT MAX(C1,2) + MIN() COUNT COUNT EACH AS C2 FROM",
                 "SELECT 1 + 1 AS C1 FROM ( SELECT 1 AS FOO, 2 AS BAR )"]

        self.run_tests(tests)

    def test_negative(self):
        tests = ["SELECT >",
                 "SELECT @@@ B",
                 "SELECT @ 2 - 1"]

        self.run_tests_negative(tests)

    def test_pyser_xml(self):
        root = minidom.parse(os.path.join('test', 'metrics.xml'))
        tests = []

        for counter in root.getElementsByTagName('counter'):
            tests.append(counter.getAttribute('comment'))

        self.run_tests(tests)


class ParserTest(TestCase):

    def run_tests(self, tests):
        for test in tests:
            root = parser.build_tree(lexer.parse(test))

            logger.info('Pyser Query: %s -> %s' % (test, root))

    def run_tests_negative(self, tests):
        for test in tests:
            logger.info('Pyser Query: %s' % test)
            self.assertRaises(ParserError, parser.build_tree, lexer.parse(test))

    def test_parser(self):
        tests = ["SELECT 1 + 1 * 1",
                 "SELECT C1 + C2 FROM ( SELECT 4 AS C1, 1 AS C2 ) "]
        self.run_tests(tests)

    def test_negative(self):
        tests = ["SELECT C2 FROM ( SELECT 5 AS C1"]

        self.run_tests_negative(tests)


class InterpreterTest(TestCase):

    def run_tests(self, tests):
        for test in tests:
            logger.info('%s == %s' % (test.code, test.result))
            self.assertEqual(test.result, test.run())

    def run_tests_negative(self, tests):
        for test in tests:
            logger.info('Pyser Query: %s' % test.code)
            logger.indent_push()
            self.assertRaises(InterpreterError, test.run)
            logger.indent_pop()

    def test_not_found(self):
        tests = [Test("SELECT SUM COUNT EACH FROM ( SELECT DISTINCT EACH '[xyzw]+' FROM ( "
                      "SELECT 'dcl_issssnput\s+v\d+.[xyzw]+' ) )",
                      result=0)]

        self.run_tests(tests)

    def test_arithmetic_operations(self):
        tests = [Test('SELECT 11 + 13', 24),
                 Test('SELECT 11 - 9', 2),
                 Test('SELECT 2 * 3', 6),
                 Test('SELECT 2 ^ 3', 8),
                 Test('SELECT 2 ** 3', 8),
                 Test('SELECT 8 / 4', 2),
                 Test('SELECT 10 % 6', 4)]

        self.run_tests(tests)

    def test_functions(self):
        tests = [Test('SELECT MAX(10, 100)', 100),
                 Test('SELECT MIN(10, 100)', 10),
                 Test('SELECT REPLACE(1, 100) FROM ( SELECT MAX(0, 1) )', 100),
                 Test('SELECT SUM(1, 2, 3)', 6)]

        self.run_tests(tests)

    def test_identifiers(self):
        tests = [Test('SELECT C1 FROM ( SELECT MAX(2, 50) AS C1 )', 50)]

        self.run_tests(tests)

    def test_labeled_arithmetic_operations(self):
        tests = [Test('SELECT C1 + C2 FROM ( SELECT 5 AS C1, 2 AS C2 )', 7)]

        self.run_tests(tests)

    def test_labeled_functions(self):
        tests = [Test('SELECT MAX(C1, C2) FROM ( SELECT 5 AS C1, 100 AS C2 )', 100)]

        self.run_tests(tests)

    def test_negative(self):
        tests = [Test("SELECT C1 FROM ( SELECT 5 AS C2 )"),
                 Test("SELECT ("),
                 Test("SELECT ) C1 FROM ( SELECT 5 AS C1 )"),
                 Test("SELECT *")]

        self.run_tests_negative(tests)

    def test_html_entities(self):
        tests = [Test("SELECT FOO + BAR * 4 FROM &#10;(SELECT 4 AS FOO, 3 AS BAR)",
                      result=16)]

        self.run_tests(tests)

    def test_backward_compatibility(self):
        tests = [
            Test("SELECT '\d+' FROM (SELECT '\[\d+\]' FROM (SELECT 'dcl_constantbuffer cb0\[\d+\]'))LIMIT 1",
                 file_path='test/PS.asm', result=18),

            Test("SELECT SUM FROM (SELECT COUNT EACH DISTINCT EACH '[xyzw]+' "
                 "FROM (SELECT 'cb0\[\d+\].[xyzw]+' FROM (SELECT 'mad[ a-zA-Z0-9-,\.\[\]]+')))",
                 file_path='test/PS.asm', result=13),

            Test("SELECT COUNT DISTINCT '\d+' FROM (SELECT '[xyzw]+\s+\d+' "
                 "FROM (SELECT '\/\/ [A-Z]+[a-zA-Z_]+\s+\d+[\s+\w+\d+]+$' FROM (SELECT 'Input.*Output')))",
                 file_path='test/PS.asm', result=8),

            Test("SELECT SUM FROM (SELECT COUNT EACH DISTINCT EACH '[xyzw]+' "
                 "FROM (SELECT DISTINCT 'cb0\[\d+\]\.[xyzw]+' FROM (SELECT 'mad[ a-zA-Z0-9-,\.\[\]]+$')))",
                 file_path='test/PS.asm', result=10),

            Test("SELECT COUNT FROM (SELECT '\/\/ [A-Z]+ [ \da-z0-9A-Z]+$'FROM (SELECT 'Input.*Output'))",
                 file_path='test/VS.asm', result=7),

            Test("SELECT COUNT '\/\/ [A-Z]+ [ \da-z0-9A-Z]+$'FROM (SELECT 'Input.*\/\/.\/\/$')",
                 file_path='test/VS.asm', result=7),

            Test("SELECT COUNT FROM (SELECT "
                 "'\/\/ [A-Z]+[a-zA-Z_]+\s+\d+\s+\w+\s+\d+\s+\w+\s+\w+\s+\w+\s*$'FROM (SELECT 'Output.*'))",
                 file_path='test/VS.asm', result=2),

            Test("SELECT COUNT '\/\/ [A-Z]+[a-zA-Z_]+\s+\d+[\s\d\w]+$' FROM (SELECT 'Output.*\/\/$')",
                 file_path='test/VS.asm', result=2)
        ]

        self.run_tests(tests)


if __name__ == '__main__':
    unittest.main()