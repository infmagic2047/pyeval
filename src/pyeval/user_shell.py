import ast
import symtable
import sys
import traceback


class _NameAttributeFinder(ast.NodeVisitor):
    def visit_Attribute(self, node):
        if not isinstance(node.value, ast.Name):
            return self.generic_visit(node.value)
        return [node.value.id]

    def generic_visit(self, node):
        result = []
        for value in ast.iter_child_nodes(node):
            result += self.visit(value)
        return result


class UserShell:
    def __init__(self, *, print_file=sys.stdout):
        self.user_globals = {}
        self.user_locals = {}
        self._print_file = print_file

    def execute_code(self, code):
        try:
            mod, table = self._parse_code(code)
            mod = self._transform_ast(mod, table)
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
        table = symtable.symtable(code, "<input>", "exec")
        return mod, table

    def _transform_ast(self, mod, table):
        visitor = _NameAttributeFinder()
        names = set(visitor.visit(mod))
        defined_symbols = set(
            x.get_name()
            for x in table.get_symbols()
            if x.is_assigned() or x.is_imported() or x.is_declared_global()
        )
        names -= defined_symbols

        # Sort the names to be predictable
        import_names = [ast.alias(name=x, asname=None) for x in sorted(names)]
        stmt = ast.Import(names=import_names)
        mod.body.insert(0, stmt)
        ast.fix_missing_locations(mod)
        return mod
