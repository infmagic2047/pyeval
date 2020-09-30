import ast
import sys
import traceback


class UserShell:
    def __init__(self, *, print_file=sys.stdout):
        self.user_globals = {}
        self.user_locals = {}
        self._print_file = print_file

    def execute_code(self, code):
        try:
            mod = self._parse_code(code)
        except SyntaxError:
            traceback.print_exc(limit=0, file=self._print_file)
            return
        for stmt in mod.body:
            if isinstance(stmt, ast.Expr):
                # Compile as expression so we can get the result
                node = ast.Expression(body=stmt.value, type_ignores=[])
                mode = "eval"
            else:
                node = ast.Module(body=[stmt], type_ignores=[])
                mode = "exec"
            code = compile(node, "<input>", mode, dont_inherit=True)
            try:
                result = eval(code, self.user_globals, self.user_locals)
            except BaseException:
                traceback.print_exc(limit=-1, file=self._print_file)
                return
            if result is not None:
                print(result, file=self._print_file)

    def _parse_code(self, code):
        mod = ast.parse(code, "<input>", "exec")
        return mod
