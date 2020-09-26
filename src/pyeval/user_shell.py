import ast
import sys


class UserShell:
    def __init__(self, *, print_file=sys.stdout):
        self.user_globals = {}
        self.user_locals = {}
        self._print_file = print_file

    def execute_code(self, code):
        mod = self._parse_code(code)
        for stmt in mod.body:
            if isinstance(stmt, ast.Expr):
                # Compile as expression so we can get the result
                node = ast.Expression(body=stmt.value, type_ignores=[])
                mode = "eval"
            else:
                node = ast.Module(body=[stmt], type_ignores=[])
                mode = "exec"
            # TODO: handle exceptions
            code = compile(node, "<input>", mode, dont_inherit=True)
            result = eval(code, self.user_globals, self.user_locals)
            if result is not None:
                print(result, file=self._print_file)

    def _parse_code(self, code):
        # TODO: handle exceptions
        mod = ast.parse(code, "<input>", "exec")
        return mod
