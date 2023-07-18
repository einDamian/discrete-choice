from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache, cached_property

from src.model.data.functions.ErrorReport import ErrorReport
from src.model.data.functions.ErrorReport import StringMarker
from src.model.data.functions.Interval import Interval
from src.model.data.functions.GroupMap import GroupMap
from src.config import ConfigExpressionErrors as Config

import ast


@dataclass(frozen=True)
class FunctionalExpression:
    """
    Input expressions without label. Maintains the error checking of the expression.

    Attributes:
        expression: Input string being evaluated.
        __DEFAULT_VARIABLES: Additional functionality usable inside expressions.
    """
    expression: str

    __DEFAULT_VARIABLES = {
        'Interval': Interval,
        'GroupMap': GroupMap
    }

    __WHITE_LISTED_BUILTINS = {
        'abs': abs,
        'divmod': divmod,
        'max': max,
        'min': min,
        'pow': pow,
        'range': range,
        'set': set,
        'sum': sum,
    }

    @cached_property
    def __compiled(self):
        """
        Compile the expression. Used for getting information from the compiler.
        """
        return compile(self.expression, '<str>', 'eval')

    def eval(self, **variables):
        """
        Evaluate the expression.
        :param variables: Usable variables in the expression.
        :return: Evaluation result.
        """
        return eval(self.expression, {"__builtins__": self.__WHITE_LISTED_BUILTINS},
                    FunctionalExpression.__DEFAULT_VARIABLES | variables)

    def __get_syntax_tree(self):
        tree = ast.parse(self.expression)
        return tree

    def __check_syntax(self) -> set[StringMarker]:
        syntax_errors = set()
        syntax_errors |= self.__check_blacklisted_words()
        syntax_errors |= self.__check_bracket_count()
        try:
            compile(self.expression, '<str>', 'eval')
        except SyntaxError as e:
            # check if error already found
            found = False
            for error in syntax_errors:
                if e.offset == error.begin and e.end_offset == error.end:
                    found = True
                    break
            if not found:
                syntax_errors.add(StringMarker(Config.ERROR_INVALID_SYNTAX, e.offset-1,
                                               (e.end_offset-1) % (len(self.expression)+1), Config.COLOR_HEX))
        return syntax_errors

    def __check_blacklisted_words(self) -> set[StringMarker]:
        blacklist_errors = set()
        function_name_regex = "[a-zA-Z0-9_]"

        current = ''
        words = list()
        for i in range(len(self.expression)):
            if re.match(function_name_regex, self.expression[i]):
                current += self.expression[i]
            elif current is not '':
                words.append((current, i - len(current), i))
                current = ''
        if current is not '':
            words.append((current, len(self.expression) - len(current), len(self.expression)))
        for word in words:
            if word[0] in __builtins__ and word[0] not in self.__WHITE_LISTED_BUILTINS:
                blacklist_errors.add(StringMarker(Config.ERROR_ILLEGAL_FUNCTION, word[1], word[2], Config.COLOR_HEX))
        return blacklist_errors

    def __check_bracket_count(self) -> set[StringMarker]:
        errors = set()
        brackets = [('(', ')'), ('{', '}'), ('[', ']')]
        expression = self.expression
        for pair in brackets:
            stack = list()
            for i in range(len(self.expression)):
                if expression[i] == pair[0]:
                    stack.append(i)
                elif expression[i] == pair[1]:
                    if len(stack) > 0:
                        stack.pop()
                    else:
                        errors.add(StringMarker(Config.ERROR_UNMATCHED_BRACKET, i, i+1, Config.COLOR_HEX))
                continue
            for index in stack:
                errors.add(StringMarker(Config.ERROR_BRACKET_NOT_CLOSED, index, index+1, Config.COLOR_HEX))
        return errors

    def __check_variables(self, **variables) -> set[StringMarker]:
        class VariableVisitor(ast.NodeVisitor):
            def __init__(self):
                self.var_nodes = list()

            def visit_Name(self, node):
                self.var_nodes.append(node)
                return node

        syntax_tree = self.__get_syntax_tree()
        visitor = VariableVisitor()
        visitor.visit(syntax_tree)
        found_errors = set()
        for variable in visitor.var_nodes:
            # variable name does not exist
            if variable.id not in variables:
                marker = StringMarker(Config.ERROR_VARIABLE_NON_EXISTENT.format(variable.id), variable.col_offset,
                                      variable.end_col_offset, Config.COLOR_HEX)
                found_errors.add(marker)
                continue
            # search for cyclic dependencies
            # TODO: fix this messy catch
            try:  # catch errors
                cyclic_dependencies = self.__check_cyclic_dependencies(variable.id, **variables)
                if cyclic_dependencies:
                    marker = StringMarker(Config.ERROR_CYCLIC_DEPENDENCY.format(cyclic_dependencies[0]), variable.col_offset,
                                          variable.end_col_offset, Config.COLOR_HEX)
                    found_errors.add(marker)
                    continue
            except (SyntaxError, AttributeError):
                marker = StringMarker(Config.ERROR_INVALID_VARIABLE.format(variable.id),
                                      variable.col_offset, variable.end_col_offset, Config.COLOR_HEX)
                found_errors.add(marker)
                continue
            # variable is invalid
            # TODO: fix for default variables
            if not hasattr(variables.get(variable.id), 'get_error_report'):
                continue
            if not variables.get(variable.id).get_error_report(**variables).valid:
                marker = StringMarker(Config.ERROR_INVALID_VARIABLE.format(variable.id), variable.col_offset,
                                      variable.end_col_offset, Config.COLOR_HEX)
                found_errors.add(marker)
                continue
        return found_errors

    @staticmethod
    def __check_cyclic_dependencies(label, **variables) -> list[list[str]]:
        cycles = list()

        def depth_search(variable_name, path):
            variable_expr = variables.get(variable_name)
            # TODO: fix for default variables
            if not hasattr(variable_expr, 'variables'):
                return
            dependencies = variable_expr.variables
            for dependency in dependencies:
                # cycle detected
                if dependency in path:
                    cycle = path.copy()
                    cycle.append(dependency)
                    cycles.append(cycle)
                    return
                # recursive step
                path.append(dependency)
                depth_search(dependency, path)
                path.pop()

        depth_search(label, [label])
        return cycles

    @lru_cache
    def get_error_report(self, **variables) -> ErrorReport:
        """
        Construct a report containing all found errors in the expression.
        Any errors make the expression invalid and should prevent execution.
        :param variables: Usable variables in the expression.
        :return: Report containing all found errors.
        """
        variables |= FunctionalExpression.__DEFAULT_VARIABLES
        found_errors = set()
        # check label (not possible)

        # check blacklisted words

        # check syntax
        found_errors |= self.__check_syntax()

        # any of the above errors make further checking impossible
        if found_errors:
            return ErrorReport(False, found_errors)

        # check used variable names for existence, cyclic dependencies and validity
        found_errors |= self.__check_variables(**variables)

        if found_errors:
            return ErrorReport(False, found_errors)
        else:
            return ErrorReport(True, set())

    @cached_property
    def variables(self) -> set[str]:
        """
        Find all used variables inside the expression
        :return: Named variables without
        """
        return set(self.__compiled.co_names) - FunctionalExpression.__DEFAULT_VARIABLES.keys()  # TODO: add other vars?

    @lru_cache
    def type(self, **variables) -> type:
        return type(self.eval(**variables))
