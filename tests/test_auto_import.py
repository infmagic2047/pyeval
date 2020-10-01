import ast
import inspect
import itertools

import pytest

from pyeval.code_transform import AutoImportTransformer


def _ast_equal_inner(node1, node2):
    fields = {
        name
        for name, _ in itertools.chain(ast.iter_fields(node1), ast.iter_fields(node2))
    }
    for name in fields:
        value1 = getattr(node1, name)
        value2 = getattr(node2, name)
        if not ast_equal(value1, value2):
            return False
    return True


def ast_equal(node1, node2):
    if type(node1) != type(node2):
        return False
    if isinstance(node1, ast.AST):
        return _ast_equal_inner(node1, node2)
    if isinstance(node1, list):
        return len(node1) == len(node2) and all(
            ast_equal(x, y) for x, y in zip(node1, node2)
        )
    return node1 == node2


def test_ast_equal_equal():
    code = "a = 1; a + b.c"
    mod1 = ast.parse(code)
    mod2 = ast.parse(code)
    assert ast_equal(mod1, mod2)


@pytest.mark.parametrize(
    "code1, code2",
    [
        pytest.param("a = 1", "b + c", id="structure"),
        pytest.param("a = 1; a + b.c", "a = 2; a + b.c", id="value"),
        pytest.param("a = 1; b = 2", "b = 2; a = 1", id="order"),
    ],
)
def test_ast_equal_not_equal(code1, code2):
    mod1 = ast.parse(code1)
    mod2 = ast.parse(code2)
    assert not ast_equal(mod1, mod2)


@pytest.mark.parametrize(
    "code, added_code",
    [
        pytest.param("math.sin(1)", "import math", id="simple_1"),
        pytest.param("a.b + c.d.e", "import a, c", id="simple_2"),
        pytest.param("a + b().c", "", id="no_import"),
        pytest.param("math = foo; math.sin(1)", "", id="defined"),
        pytest.param("import math; math.sin(1)", "", id="already_imported"),
        pytest.param("int.from_bytes(foo)", "", id="builtin"),
        pytest.param(
            inspect.cleandoc(
                """
                a = math.sin(1) + math.cos(1)
                print(a, a.as_integer_ratio(), file=sys.stdout)
                """
            ),
            "import math, sys",
            id="complex_multiple_import",
        ),
        pytest.param(
            inspect.cleandoc(
                """
                def f(x):
                    z = something
                    return x.foo + y.foo + z.foo + w.foo
                y = something
                """
            ),
            "import w",
            id="complex_function_scope",
        ),
    ],
)
def test_auto_import(code, added_code):
    transformer = AutoImportTransformer()
    mod = ast.parse(code)
    mod = transformer.apply(mod)
    expected_code = added_code + "\n" + code
    expected_mod = ast.parse(expected_code)
    assert ast_equal(mod, expected_mod)
