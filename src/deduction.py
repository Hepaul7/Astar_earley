from dataclasses import dataclass
from typing import Tuple, Union, Self, List

from cfg import GrammarPoint, Symbol, Grammar, StarPoint
from node import InputString


@dataclass(frozen=True)
class DeductionSpan:
    point: Union[GrammarPoint, StarPoint, Symbol]
    span: Tuple[int, int]

    def fmt(self, grammar: Grammar) -> str:
        b, e = self.span
        if type(self.point) is GrammarPoint:
            return f"{grammar.fmt_point(self.point)} [{b}, {e})"
        elif type(self.point) is StarPoint:
            return f"{grammar.symbols[self.point.sym].symbol()}★ [{b}, {e})"
        else:
            return f"{grammar.symbols[self.point].symbol()} [{b}, {e})"


@dataclass(frozen=True)
class DeductionNode:
    span: DeductionSpan
    children: List[Self]

    def fmt_tree(self, grammar: Grammar, depth: int = 0, s: Union[InputString, None] = None) -> List[str]:
        b, e = self.span.span
        me = f"{'\t' * depth}{self.span.fmt(grammar)}"
        if s is not None:
            me = f"{me} {s.sep.join([c.symbol() for c in s.nodes[b:e]])}"
        nlist = [me]
        for c in self.children:
            nlist.extend(c.fmt_tree(grammar, depth + 1, s))
        return nlist
