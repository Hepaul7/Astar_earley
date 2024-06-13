import unittest
from unittest import TestCase

from bidict import bidict

import naive_earley as naive
from node import NonTerminal, Terminal


def toy_grammar() -> naive.Grammar:
    # TODO: an efficient way of adding terminal/nonterminal automatically to the cfg
    g = naive.Grammar()
    g.add_symbol(
        NonTerminal("A")).add_symbol(
        Terminal("a")).add_symbol(
        Terminal("b")).add_symbol(
        Terminal("c"))
    g.add_rule(
        (NonTerminal("<start>"), [NonTerminal("A"), NonTerminal("A")])).add_rule(
        (NonTerminal("A"), [NonTerminal("A"), Terminal("a")])).add_rule(
        (NonTerminal("A"), [Terminal("b"), NonTerminal("A")])).add_rule(
        (NonTerminal("A"), [Terminal("c")]))
    return g


class TestGrammar(TestCase):
    def test_simple(self):
        g = toy_grammar()

        print("SYMBOLZ:", g.fmt_all_symbols())
        print("RULEZ:", g.fmt_all_rules())
        assert g.symbols == bidict({
            0: NonTerminal("<start>"),
            1: Terminal("\0"),
            2: NonTerminal("A"),
            3: Terminal("a"),
            4: Terminal("b"),
            5: Terminal("c")})
        assert set(g.fmt_all_rules()) == {'<start> → AA', 'A → Aa|bA|c'}


if __name__ == '__main__':
    unittest.main()
