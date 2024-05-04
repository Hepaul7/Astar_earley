import unittest
from unittest import TestCase

import fast_earley as fast
import naive_earley as naive
from node import Terminal, NonTerminal, InputString


def toy_grammar() -> naive.Grammar:
    # TODO: an efficient way of adding terminal/nonterminal automatically to the cfg
    g = naive.Grammar()
    g.add_symbol(
        NonTerminal("A"), False).add_symbol(
        Terminal("a"), True).add_symbol(
        Terminal("b"), True).add_symbol(
        Terminal("c"), True)
    g.add_rule(
        (NonTerminal("<start>"), [NonTerminal("A"), NonTerminal("A")])).add_rule(
        (NonTerminal("A"), [NonTerminal("A"), Terminal("a")])).add_rule(
        (NonTerminal("A"), [Terminal("b"), NonTerminal("A")])).add_rule(
        (NonTerminal("A"), [Terminal("c")]))
    return g


def grammar_1() -> naive.Grammar:
    g = naive.Grammar()
    g.add_symbol(
        Terminal("book"), True).add_symbol(
        Terminal("that"), True).add_symbol(
        Terminal("flight"), True).add_symbol(
        Terminal("a"), True).add_symbol(
        Terminal("the"), True).add_symbol(
        Terminal("meal"), True).add_symbol(
        Terminal("include"), True).add_symbol(
        Terminal("prefer"), True).add_symbol(
        NonTerminal("NP"), False).add_symbol(
        NonTerminal("VP"), False).add_symbol(
        NonTerminal("Det"), True).add_symbol(
        NonTerminal("Nominal"), True).add_symbol(
        NonTerminal("Noun"), True).add_symbol(
        NonTerminal("Verb"), True)

    g.add_rule(
        (NonTerminal("<start>"), [NonTerminal("NP"), NonTerminal("VP")])).add_rule(
        (NonTerminal("<start>"), [NonTerminal("VP")])).add_rule(
        (NonTerminal("NP"), [NonTerminal("Det"), NonTerminal("Nominal")])).add_rule(
        (NonTerminal("Nominal"), [NonTerminal("Noun")])).add_rule(
        (NonTerminal("VP"), [NonTerminal("Verb")])).add_rule(
        (NonTerminal("VP"), [NonTerminal("Verb"), NonTerminal("NP")])).add_rule(
        (NonTerminal("Det"), [Terminal("that")])).add_rule(
        (NonTerminal("Noun"), [Terminal("book")])).add_rule(
        (NonTerminal("Noun"), [Terminal("flight")])).add_rule(
        (NonTerminal("Verb"), [Terminal("book")])
    )

    return g


class TestNaiveEarley(TestCase):
    def test_simple(self):
        g = toy_grammar()
        p = naive.Earley(g)
        input_strings = InputString("cac")
        for c in input_strings.nodes:
            p.feed(c)
        p.feed(Terminal("\0"))

        print('CHART:')
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

        assert ([c.fmt(p.grammar) for c in p.complete_items()] == ['<start> → AA• [0, 3)'])
        fin = p.complete_items()[0]
        dt_repr = p.trace_deduction(fin).fmt_tree(p.grammar, s=input_strings)
        print('DERIVATION TREE:\n', '\n'.join(dt_repr))
        assert dt_repr == [
            "<start> → AA• [0, 3) cac",
            "\tA → Aa• [0, 2) ca",
            "\t\tA → c• [0, 1) c",
            "\t\t\tc [0, 1) c",
            "\t\ta [1, 2) a",
            "\tA → c• [2, 3) c",
            "\t\tc [2, 3) c",
        ]

    def test_reject(self):
        grammar = toy_grammar()
        parser = naive.Earley(grammar)
        input_strings = InputString("aba").nodes
        for c in input_strings:
            parser.feed(c)
        parser.feed(Terminal("\0"))

        for index, state_set in enumerate(parser.chart):
            state_set_str = set(parser.grammar.fmt_point(state.point) for state in state_set)
            print(f"{index}\t: {state_set_str}")

        # Assertions
        assert len(parser.chart) == 4
        assert (set(parser.grammar.fmt_point(state.point) for state in parser.chart[0]) ==
                {'<start> → •AA', 'A → •bA', 'A → •c', 'A → •Aa'})
        assert (set(parser.grammar.fmt_point(state.point) for state in parser.chart[1]) ==
                set())
        assert (set(parser.grammar.fmt_point(state.point) for state in parser.chart[2]) ==
                set())
        assert (set(parser.grammar.fmt_point(state.point) for state in parser.chart[3]) ==
                set())

    def test_long_terminal(self):
        grammar = grammar_1()
        parser = naive.Earley(grammar)
        sep = ' '
        input_strings = InputString("book that flight", sep)
        for c in input_strings.nodes:
            parser.feed(c)
        parser.feed(Terminal("\0"))
        for index, state_set in enumerate(parser.chart):
            state_set_str = set(parser.grammar.fmt_point(state.point, sep) for state in state_set)
            print(f"{index}\t: {state_set_str}")

        assert len(parser.chart) == 4
        assert (set(parser.grammar.fmt_point(s.point, sep) for s in parser.chart[0]) ==
                {'NP → •Det Nominal', 'Verb → •book', 'VP → •Verb NP', 'VP → •Verb', '<start> → •NP VP', 'Det → •that',
                 '<start> → •VP'})
        assert (set(parser.grammar.fmt_point(s.point, sep) for s in parser.chart[1]) ==
                {'Verb → book•', 'VP → Verb•NP', 'Det → •that', '<start> → VP•', 'VP → Verb•', 'NP → •Det Nominal'})
        assert (set(parser.grammar.fmt_point(s.point, sep) for s in parser.chart[2]) ==
                {'Noun → •flight', 'Det → that•', 'Noun → •book', 'Nominal → •Noun', 'NP → Det•Nominal'})
        assert (set(parser.grammar.fmt_point(s.point, sep) for s in parser.chart[3]) ==
                {'NP → DetNominal•', 'Noun → flight•', '<start> → VP•', 'VP → VerbNP•', 'Nominal → Noun•'})

        assert ([c.fmt(parser.grammar) for c in parser.complete_items()] == ['<start> → VP• [0, 3)'])
        fin = parser.complete_items()[0]
        dt_repr = parser.trace_deduction(fin).fmt_tree(parser.grammar, s=input_strings)
        print('DERIVATION TREE:\n', '\n'.join(dt_repr))
        assert dt_repr == [
            "<start> → VP• [0, 3) book that flight",
            "\tVP → VerbNP• [0, 3) book that flight",
            "\t\tVerb → book• [0, 1) book",
            "\t\t\tbook [0, 1) book",
            "\t\tNP → DetNominal• [1, 3) that flight",
            "\t\t\tDet → that• [1, 2) that",
            "\t\t\t\tthat [1, 2) that",
            "\t\t\tNominal → Noun• [2, 3) flight",
            "\t\t\t\tNoun → flight• [2, 3) flight",
            "\t\t\t\t\tflight [2, 3) flight",
        ]


class TestFastEarley(TestCase):
    def test_simple(self):
        g = toy_grammar()
        p = fast.Earley(g)
        input_strings = InputString("cac")
        for c in input_strings.nodes:
            p.feed(c)
        p.feed(Terminal("\0"))

        assert len(p.chart) == 4
        assert (set(p.grammar.fmt_point(s.point) for s in p.chart[0]) ==
                {'<start> → •AA', 'A → •c', 'A → •Aa', 'A → •bA', 'A → •★'})
        assert (set(p.grammar.fmt_point(s.point) for s in p.chart[1]) ==
                {'A → c•', 'A → ★•', '<start> → A•A', 'A → A•a', 'A → •Aa',
                 'A → •bA', 'A → •c', 'A → •★', 'A → •Aa'})
        assert (set(p.grammar.fmt_point(s.point) for s in p.chart[2]) ==
                {'A → Aa•', 'A → •bA', 'A → •Aa', 'A → A•a', '<start> → A•A', 'A → •c', 'A → ★•', 'A → •★'})
        assert (set(p.grammar.fmt_point(s.point) for s in p.chart[3]) ==
                {'<start> → AA•', 'A → c•', 'A → A•a', 'A → ★•'})
        for k, st in enumerate(p.chart):
            st_str = set(p.grammar.fmt_point(s.point) for s in st)
            print(f"{k}\t: {st_str}")

        for k, v in p.deduced_by.items():
            print(f"{k.fmt(p.grammar)} is deduced by {v.fmt(p.grammar)}")
        assert ([c.fmt(p.grammar) for c in p.complete_items()] == ['<start> → AA• [0, 3)'])
        fin = p.complete_items()[0]
        dt_repr = p.trace_deduction(fin).fmt_tree(p.grammar, s=input_strings)
        print('DERIVATION TREE:\n', '\n'.join(dt_repr))
        assert dt_repr == [
            "<start> → AA• [0, 3) cac",
            "\tA★ [0, 2) ca",
            "\t\tA → Aa• [0, 2) ca",
            "\t\t\tA★ [0, 1) c",
            "\t\t\t\tA → c• [0, 1) c",
            "\t\t\t\t\tc [0, 1) c",
            "\t\t\ta [1, 2) a",
            "\tA★ [2, 3) c",
            "\t\tA → c• [2, 3) c",
            "\t\t\tc [2, 3) c",
        ]


if __name__ == '__main__':
    unittest.main()
