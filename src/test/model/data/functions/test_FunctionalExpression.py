from __future__ import annotations

from src.model.data.functions.FunctionalExpression import FunctionalExpression
from src.model.data.functions.ErrorReport import ErrorReport
from src.model.data.functions.StringMarker import StringMarker

import unittest
from parameterized import parameterized
import pandas as pd


class TestFunctionalExpression(unittest.TestCase):
    __ERROR_COLOR = 0xFF644E

    @parameterized.expand([
        ('a == b', {'a', 'b'}),
        ('sum(x)', {'x'}),
        ('Interval(x)', {'x'}),
        ('GroupMap(x, y)(z)', {'x', 'y', 'z'}),
        ('f(x)', {'f', 'x'}),
        ('Interval(x)', {'x'}),
        ('(lambda x: x+1)(z)', {'z'})
    ])
    def test_variables(self, expr: str, variables: set[str]):
        self.assertSetEqual(FunctionalExpression(expr).variables, variables)

    @parameterized.expand([
        ('bool', 'a == b', {'a': 1, 'b': 2}, bool),
        ('int', '1 + 3 * x', {'x': 15}, int),
        ('pd.Series', '1 + 3 * x', {'x': pd.Series(range(10))}, pd.Series),
        ('groupmap_range1', 'GroupMap(range(0, 2), range(2, 4), range(4, 6))(x)', {'x': 5}, int),
    ])
    def test_type(self, name: str, expr: str, variables: dict[str, object], type_: type):
        self.assertEqual(FunctionalExpression(expr).type(**variables), type_)

    @parameterized.expand([
        ('eqeqeq', 'a === b', {'a': 1, 'b': 2},
         ErrorReport(False, [StringMarker('SyntaxError: invalid syntax', 4, 5, __ERROR_COLOR)])),

        ('unknown_var', 'a == b', {'b': 2},
         ErrorReport(False, [StringMarker('NameError: name \'a\' is not defined', 0, 1, __ERROR_COLOR)])),

        ('unknown_vars', 'a == b', {'b': 2},
         ErrorReport(False, [StringMarker('NameError: name \'a\' is not defined', 0, 1, __ERROR_COLOR),
                             StringMarker('NameError: name \'b\' is not defined', 5, 6, __ERROR_COLOR)])),

        ('brackets1', ')(', {'b': 2},
         ErrorReport(False, [StringMarker('SyntaxError: unmatched \')\'', 0, 1, __ERROR_COLOR)])),

        ('brackets2', '((', {'b': 2},
         ErrorReport(False, [StringMarker('SyntaxError: \'(\' was never closed', 1, 2, __ERROR_COLOR)])),

        ('contains_set', 's in set({\'abc\', \'def\', \'ghi\'})', {'s': 'def'}, ErrorReport(True, [])),
    ])
    def test_error_report(self, name: str, expr: str, variables: dict[str, object], report: ErrorReport):
        self.assertEqual(FunctionalExpression(expr).get_error_report(**variables), report)

    @parameterized.expand([
        ('eq_false', 'a == b', {'a': 1, 'b': 2}, False),
        ('eq_true', 'a == b', {'a': 'qwertz', 'b': 'qwertz'}, True),
        ('add', 'a + b', {'a': 'abc', 'b': 'def'}, 'abcdef'),
        ('floordiv', 'a // b', {'a': 5, 'b': 2.3}, 2),
        ('pow_2**2', 'a ** b', {'a': 2, 'b': 2}, 4),
        ('pow_2**3', 'a ** b', {'a': 2, 'b': 3}, 8),
        ('pow_64**(1/2)', 'a ** b', {'a': 64, 'b': 1/2}, 8),
        ('sum_gen', 'sum(g)', {'g': (i ** 2 for i in range(10))}, 285),
        ('contains_set', 's in set({\'abc\', \'def\', \'ghi\'})', {'s': 'def'}, True),
        ('contains_interval1', 'x in Interval(0, None)', {'x': -3}, False),
        ('contains_interval2', 'x in Interval(0, 2)', {'x': 2}, False),
        ('contains_interval3', 'x in Interval(0, 2)', {'x': 1.99}, True),
        ('groupmap_range1', 'GroupMap(range(0, 2), range(2, 4), range(4, 6))(x)', {'x': 5}, 3),
        ('groupmap_range2', 'GroupMap(range(0, 2), range(2, 4), range(4, 6))(x)', {'x': -10}, None),
        ('groupmap_interval1', 'GroupMap(Interval(0, 2), Interval(2, 4), Interval(4, 6))(x)', {'x': 3.9}, 2),
        ('groupmap_interval2', 'GroupMap(Interval(None, 2), Interval(2, 4), Interval(4, 6))(x)', {'x': -10}, 1),
        ('groupmap_interval3', 'GroupMap(Interval(None, 2), Interval(2, 4), Interval(4, 6))(x)', {'x': 2}, None),
        ('lambda', '(lambda x: x+1)(z)', {'z': 2}, 3)
    ])
    def test_eval(self, name: str, expr: str, variables: dict[str, object], val: object):
        self.assertEqual(FunctionalExpression(expr).eval(**variables), val)

    @parameterized.expand([
        ('while', 'while True: pass', {}, SyntaxError),
        ('import1', 'import math', {}, SyntaxError),
        ('import2', 'from math import floor', {}, SyntaxError),
        ('import3', '__import__(\'math\').floor(2.5)', {}, NameError),
        ('eval_import', 'eval("__import__(\'math\').floor(2.5)")', {}, NameError)
    ])
    def test_security(self, name: str, expr: str, variables: dict[str, object], expected_exception):
        e = FunctionalExpression(expr)
        with self.assertRaises(expected_exception):
            e.eval(**variables)


if __name__ == '__main__':
    unittest.main()
