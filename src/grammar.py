from functools import total_ordering
from typing import Callable, Iterable, List, Tuple, Union, Self


@total_ordering
class Nonterminal:
    """
    A non-terminal symbol.
    """
    def __init__(self, symbol: str):
        """ Create a nonterminal.
        :param symbol: The symbol of the nonterminal.
        symbol is hashable and immutable, for now accept string only.
        """
        self._symbol = symbol

    def symbol(self) -> str:
        """ Get the symbol of the nonterminal.
        """
        return self._symbol

    def __eq__(self, other: Self) -> bool:
        """ Equality check.
        :param other: The other nonterminal.
        """
        return self._symbol == other.symbol()

    def __lt__(self, other: Self) -> bool:
        """ Less than operator.
        :param other: The other nonterminal.
        """
        return self._symbol < other._symbol

    def __hash__(self):
        return hash(self._symbol)


def nonterminal(symbol: str) -> Nonterminal:
    """ Create a nonterminal.
    :param symbol: The symbol of the nonterminal.
    """
    return Nonterminal(symbol)


def nonterminals(*symbols: str) -> Iterable[Nonterminal]:
    """ Create a sequence of nonterminals.
    :param symbols: The symbols of the nonterminals.
    Example:
    >>> [x.symbol() for x in nonterminals('A', 'B')]
    ['A', 'B']
    """
    for symbol in symbols:
        yield nonterminal(symbol)


def is_nonterminal(item):
    """ Check if item is a nonterminal.
    """
    return isinstance(item, Nonterminal)


def is_terminal(item):
    """ Check if item is a terminal.
    Item is terminal if it is hashable and immutable, for now accept string only.
    """
    return not is_nonterminal(item) and hasattr(item, "__hash__")


class Production:
    """
    A production rule.
    """
    def __init__(self, lhs: Nonterminal, rhs: List[str | Nonterminal]):
        self._lhs = lhs
        self._rhs = tuple(rhs)

    def lhs(self) -> Nonterminal:
        """ Get the lhs of the production.
        """
        return self._lhs

    def rhs(self) -> tuple[str | Nonterminal, ...]:
        """ Get the rhs of the production.
        """
        return self._rhs

    def __len__(self) -> int:
        """ Get the length of the production.
        """
        return len(self._rhs)

    def is_nonlexical(self) -> bool:
        """ Check if the production is non-lexical.
        non-lexical: all rhs are nonterminals.
        """
        return all(is_nonterminal(n) for n in self._rhs)

    def is_lexical(self) -> bool:
        """ Check if the production is lexical.
        lexical: at least one terminal on rhs.
        """
        return not self.is_nonlexical()

    def __str__(self):
        """ Get the string representation of the production.
        """
        result = f'{self._lhs.symbol()} ->'
        for rhs in self._rhs:
            if isinstance(rhs, str):    # a dirty way for now
                result += f' {rhs}'
            else:
                result += f' {rhs.symbol()}'

        return result

    def __eq__(self, other: Self) -> bool:
        """ Equality check.
        """
        return self._lhs == other.lhs() and self._rhs == other.rhs()

    def __ne__(self, other):
        """ Check if not equal
        """
        return not self == other

    def __hash__(self):
        """ Get the hash of the production.
        """
        return hash((self._lhs, self._rhs))
