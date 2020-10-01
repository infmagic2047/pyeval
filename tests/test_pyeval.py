import ast
import io

from pyeval.code_transform import ASTNodeTransformer
from pyeval.user_shell import UserShell


def test_execute_code():
    buf = io.StringIO()
    user_shell = UserShell(print_file=buf)
    user_shell.execute_code("a = 1; a + 1; b = 2; a + b")
    result = buf.getvalue()
    assert result == "2\n3\n"


class _IncrementInteger(ast.NodeTransformer):
    def visit_Constant(self, node):
        if isinstance(node.value, int):
            node.value += 1
        return node


def test_code_transform():
    buf = io.StringIO()
    user_shell = UserShell(
        print_file=buf, transformers=[ASTNodeTransformer(_IncrementInteger())]
    )
    user_shell.execute_code("a = 1; a + 1; b = 2; a + b")
    result = buf.getvalue()
    assert result == "4\n5\n"
