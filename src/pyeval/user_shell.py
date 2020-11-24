import ast
import sys
import traceback


class UserShell:
    def __init__(self, *, print_file=sys.stdout, transformers=None):
        self.user_ns = {}
        self._print_file = print_file
        if transformers is None:
            transformers = []
        self._transformers = transformers

    def execute_code(self, code):
        try:
            mod = ast.parse(code, "<input>", "exec")
        except SyntaxError:
            traceback.print_exc(limit=0, file=self._print_file)
            return
        mod = self._transform_ast(mod)
        self._run_with_result_printing(mod)

    def _run_with_result_printing(self, mod):
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
                result = eval(code, self.user_ns, self.user_ns)
            except BaseException:
                traceback.print_exc(limit=-1, file=self._print_file)
                return
            if result is not None:
                print(repr(result), file=self._print_file)

    def _transform_ast(self, mod):
        for tr in self._transformers:
            mod = tr.apply(mod)
        ast.fix_missing_locations(mod)
        return mod
