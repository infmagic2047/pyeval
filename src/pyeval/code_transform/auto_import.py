import ast
import builtins
import sys

from .base import ASTTransformer


class _Scope:
    def __init__(self, is_comprehension=False):
        self._names_used = set()
        self._names_defined = set()
        self._is_comprehension = is_comprehension

    def use_name(self, name):
        self._names_used.add(name)

    def define_name(self, name):
        self._names_defined.add(name)

    def get_names_used_not_defined(self):
        return self._names_used - self._names_defined

    @property
    def is_comprehension(self):
        return self._is_comprehension


class BaseUndefinedNameFinder(ast.NodeVisitor):
    """
    Base class for undefined name finders.

    This class traverses the AST and maintains a list of defined symbols
    for each scope, but does not specify what constitutes a use of
    symbol. Subclasses should call self._use_name() to mark a name as
    used in the current scope.
    """

    def __init__(self):
        self._scopes = None
        self._visiting_annotations = False

    def _generic_visit_excluding(self, node, excludes):
        for field, value in ast.iter_fields(node):
            if field in excludes:
                continue
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, ast.AST):
                        self.visit(item)
            elif isinstance(value, ast.AST):
                self.visit(value)

    def _use_name(self, name):
        self._scopes[-1].use_name(name)

    def _define_name(self, name):
        self._scopes[-1].define_name(name)

    def _push_scope(self, is_comprehension=False):
        self._scopes.append(_Scope(is_comprehension))

    def _pop_scope(self):
        scope = self._scopes.pop()
        for name in scope.get_names_used_not_defined():
            self._use_name(name)

    def _visit_func_def(self, node):
        self._define_name(node.name)
        for value in node.args.defaults:
            self.visit(value)
        for value in node.args.kw_defaults:
            if value is not None:
                self.visit(value)
        for value in node.decorator_list:
            self.visit(value)
        self._visiting_annotations = True
        self.visit(node.args)
        self._visiting_annotations = False
        if node.returns is not None:
            self.visit(node.returns)

        self._push_scope()
        self._generic_visit_excluding(node, ["decorator_list", "returns"])
        self._pop_scope()

    visit_FunctionDef = _visit_func_def
    visit_AsyncFunctionDef = _visit_func_def

    def visit_ClassDef(self, node):
        self._define_name(node.name)
        for value in node.bases:
            self.visit(value)
        for value in node.keywords:
            self.visit(value)

        self._push_scope()
        self._generic_visit_excluding(node, ["bases", "keywords"])
        self._pop_scope()

    def visit_Lambda(self, node):
        for value in node.args.defaults:
            self.visit(value)
        for value in node.args.kw_defaults:
            self.visit(value)

        self._push_scope()
        self.generic_visit(node)
        self._pop_scope()

    def _visit_comprehension(self, node):
        for gen in node.generators:
            self.visit(gen.iter)
            self._push_scope(True)
            self._generic_visit_excluding(gen, ["iter"])

        self._generic_visit_excluding(node, ["generators"])

        for _ in node.generators:
            self._pop_scope()

    visit_GeneratorExp = _visit_comprehension
    visit_ListComp = _visit_comprehension
    visit_SetComp = _visit_comprehension
    visit_DictComp = _visit_comprehension

    def visit_arguments(self, node):
        self._generic_visit_excluding(node, ["defaults", "kw_defaults"])

    def visit_arg(self, node):
        if self._visiting_annotations:
            if node.annotation is not None:
                self.visit(node.annotation)
        else:
            self._define_name(node.arg)
            self._generic_visit_excluding(node, ["annotation"])

    def visit_Global(self, node):
        for name in node.names:
            self._define_name(name)
            # Mark as defined in the global scope as well
            self._scopes[0].define_name(name)
        self.generic_visit(node)

    def visit_Nonlocal(self, node):
        for name in node.names:
            self._define_name(name)
        self.generic_visit(node)

    def visit_Name(self, node):
        if not isinstance(node.ctx, ast.Load):
            self._define_name(node.id)
        self.generic_visit(node)

    def visit_NamedExpr(self, node):
        assert isinstance(node.target, ast.Name)
        # Define in surrounding non-comprehension scope
        for scope in reversed(self._scopes):
            if not scope.is_comprehension:
                scope.define_name(node.target.id)
                break
        self.generic_visit(node)

    def visit_ExceptHandler(self, node):
        if node.name is not None:
            self._define_name(node.name)
        self.generic_visit(node)

    def visit_alias(self, node):
        name = node.asname
        if name is None:
            name = node.name
        if "." in name:
            name = name[: name.index(".")]
        if name != "*":
            self._define_name(name)
        self.generic_visit(node)

    def visit_MatchAs(self, node):
        if node.name is not None:
            self._define_name(node.name)
        self.generic_visit(node)

    def visit_MatchStar(self, node):
        if node.name is not None:
            self._define_name(node.name)
        self.generic_visit(node)

    def visit_MatchMapping(self, node):
        if node.rest is not None:
            self._define_name(node.rest)
        self.generic_visit(node)

    def visit_Module(self, node):
        self._scopes = [_Scope()]

        self.generic_visit(node)

        names = self._scopes[0].get_names_used_not_defined()
        self._scopes = None
        return names


class UndefinedNameAttributeFinder(BaseUndefinedNameFinder):
    def visit_Attribute(self, node):
        if isinstance(node.value, ast.Name):
            self._use_name(node.value.id)
        getattr(super(), "visit_Attribute", self.generic_visit)(node)


class AutoImportTransformer(ASTTransformer):
    def __init__(self, *, verbose=False):
        self._verbose = verbose

    def apply(self, mod: ast.Module):
        undefined_references = UndefinedNameAttributeFinder().visit(mod)
        names = sorted(
            name for name in undefined_references if not hasattr(builtins, name)
        )
        if not names:
            return mod

        if self._verbose:
            print(f"Automatically importing {names}", file=sys.stderr)
        import_names = [ast.alias(name=x, asname=None) for x in names]
        stmt = ast.Import(names=import_names)
        mod.body.insert(0, stmt)
        return mod
