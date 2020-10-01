import ast
from abc import ABCMeta, abstractmethod


class ASTTransformer(metaclass=ABCMeta):
    @abstractmethod
    def apply(self, mod: ast.Module):
        return mod


class ASTNodeTransformer(ASTTransformer):
    def __init__(self, node_transformer: ast.NodeTransformer):
        self._node_transformer = node_transformer

    def apply(self, mod: ast.Module):
        mod = self._node_transformer.visit(mod)
        return mod
