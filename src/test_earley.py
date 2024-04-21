import unittest
from unittest import TestCase

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


class TestNaiveEarley(TestCase):
    def test_simple(self):
        g = toy_grammar()
        p = naive.Earley(g)
        for c in "cac":
            p.feed(c)
        p.feed("\0")

        for k, st in enumerate(p.chart):
            st_str = set(p.grammar.fmt_point(s.point) for s in st)
            print(f"{k}\t: {st_str}")

        assert len(p.chart) == 4
        assert (set(p.grammar.fmt_point(s.point) for s in p.chart[0]) ==
                {'<start> → •AA', 'A → •c', 'A → •Aa', 'A → •bA'})
        assert (set(p.grammar.fmt_point(s.point) for s in p.chart[1]) ==
                {'A → •bA', 'A → •Aa', 'A → A•a', '<start> → A•A', 'A → c•', 'A → •c'})
        assert (set(p.grammar.fmt_point(s.point) for s in p.chart[2]) ==
                {'A → Aa•', 'A → •bA', 'A → •Aa', 'A → A•a', '<start> → A•A', 'A → •c'})
        assert (set(p.grammar.fmt_point(s.point) for s in p.chart[3]) ==
                {'<start> → AA•', 'A → c•', 'A → A•a'})


if __name__ == '__main__':
    unittest.main()
