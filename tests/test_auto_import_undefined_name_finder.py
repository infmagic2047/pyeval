import ast
import sys

import pytest

from pyeval.code_transform.auto_import import BaseUndefinedNameFinder


@pytest.mark.parametrize(
    "code, defined_names",
    [
        pytest.param("x = 1", ["x"], id="assign"),
        pytest.param("y = (x := 1)", ["x", "y"], id="named_expr"),
        pytest.param("nonlocal x; global y", ["x", "y"], id="global_nonlocal"),
        pytest.param("del x, y[1]", ["x"], id="del_var"),
        pytest.param("def f(x=a, y=b): pass", ["f", "x", "y"], id="function"),
        pytest.param("class A(B): pass", ["A"], id="class"),
        pytest.param("import a, b as c", ["a", "c"], id="import"),
        pytest.param("from a import b, c as d", ["b", "d"], id="import_from"),
        pytest.param(
            "match x:\n case [a, b, *c, {1: 2, **d}]: pass",
            ["a", "b", "c", "d"],
            id="match_case",
            marks=pytest.mark.skipif(
                sys.version_info < (3, 10), reason="uses python 3.10 syntax"
            ),
        ),
    ],
)
def test_undefined_name_finder_define_names(code, defined_names, mocker):
    finder = BaseUndefinedNameFinder()
    spy = mocker.spy(finder, "_define_name")
    finder.visit(ast.parse(code))
    for name in defined_names:
        spy.assert_any_call(name)
    assert spy.call_count == len(defined_names)
