import unittest
from unittest import TestCase

from bidict import bidict

import naive_earley as naive


def toy_grammar() -> naive.Grammar:
    g = naive.Grammar()
    g.add_symbol(
        "A", False).add_symbol(
        "a", True).add_symbol(
        "b", True).add_symbol(
        "c", True)
    g.add_rule(
        ("<start>", ["A", "A"])).add_rule(
        ("A", ["A", "a"])).add_rule(
        ("A", ["b", "A"])).add_rule(
        ("A", ["c"]))
    return g


class TestGrammar(TestCase):
    def test_simple(self):
        g = toy_grammar()

        print("SYMBOLZ:", g.fmt_all_symbols())
        print("RULEZ:", g.fmt_all_rules())
        assert g.symbols == bidict({0: "<start>", 1: "\0", 2: "A", 3: "a", 4: "b", 5: "c"})
        assert set(g.fmt_all_rules()) == {'<start> → AA', 'A → Aa|bA|c'}


if __name__ == '__main__':
    unittest.main()
