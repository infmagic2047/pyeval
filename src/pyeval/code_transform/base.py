from abc import ABCMeta, abstractmethod


class ASTTransformer(metaclass=ABCMeta):
    @abstractmethod
    def apply(self, mod):
        return mod
