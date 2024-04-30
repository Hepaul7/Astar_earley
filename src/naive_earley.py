"""
The "naive" implementation of the Earley algorithm.
"""
from dataclasses import dataclass
from typing import Set, List, Tuple, TypeAlias, Self, Dict, Union

from cfg import GrammarPoint, Grammar, Symbol
from deduction import DeductionSpan, DeductionNode
from node import Terminal, NonTerminal


@dataclass(frozen=True)
class Item:
    """An `Item` represents a partial parse of a grammar rule at some point in the input string."""
    point: GrammarPoint
    """The partially parsed (i.e. dotted) rule."""
    beg: int
    """Where this parse began in the input string."""

    def proceed(self) -> Self:
        """Moves the `dot` of the item one step forward in the rule.
        PRE: `dot` must _not_ be at or past the end of the rule."""
        return Item(self.point.proceed(), self.beg)

    def deduction_span(self, end: int) -> DeductionSpan:
        return DeductionSpan(self.point, (self.beg, end))


State: TypeAlias = Set[Item]
"""A `State` is the set of all items (i.e. partially parsed rules) to be considered
for parsing the terminal symbol at a particular point in the input string."""
Chart: TypeAlias = List[State]
"""A `Chart` is the list of all the states for the input, with an extra state for the very
beginning of the string (i.e. the chart has a length of `n+1` where `n` is the input size)."""
DeductionChart: TypeAlias = Dict[DeductionSpan, DeductionSpan]
"""For an item `key`, returns one possible item `value`, the completion of which proves of this item.
The span of the prior partial parse can be computed from `key` and `value`.
TODO: Keeping a hashmap isn't very performant. Consider finding an alternative."""


@dataclass
class Earley:
    """Holds the logic to produce the various states while parsing an input string
    in a particular grammar with the Earley algorithm."""
    grammar: Grammar
    chart: Chart
    deduced_by: DeductionChart

    def __init__(self, g: Grammar):
        self.grammar = g
        self.chart = [set()]
        self.deduced_by = dict()
        start = self.grammar.symbols.inverse[NonTerminal("<start>")]
        for rule in range(len(self.grammar.rules[start])):
            self.chart[0].add(Item(GrammarPoint(start, rule, 0), 0))

    def process(self, cur_pos: int, cur_state: State, next_sym: Symbol) -> Tuple[State, State]:
        """Process all the items in `cur_state`, which represents the early state during the processing of the input
        symbol at `cur_pos` which contains a terminal symbol `next_sym`, to produce:
        1) A set of items produced by predictions and completions, and should be appended to `cur_state`.
        2) A set of items produced by scans, and should be used to construct a new state for further inputs."""

        assert next_sym in self.grammar.terminals  # ensure that `next_sym` is indeed terminal.
        old, new = set(), set()  # the two sets of Earley items as discussed earlier.
        # Go over all the items in `cur_state`
        for it in cur_state:
            dot_sym = self.grammar.get_symbol_at_point(it.point)  # the symbol right after the `dot`.
            if dot_sym is None:
                # Complete: If there is no symbol after the `dot`, we have completed this item.
                # TODO: optimise here by tracking?

                # Find any other items that _waiting_ at this item's start position for this item's generating symbol.
                # Those items can now move forward one step now.
                more = set(
                    cit.proceed() for cit in self.chart[it.beg] if
                    self.grammar.get_symbol_at_point(cit.point) == it.point.sym)
                # But these items still belongs to the current state, since no input symbol was consumed here.
                old.update(more)
                # The item `it` completes the item `nit` (it is assumed that `it` was predicted by the symbol right
                # after the `dot` in `nit`).
                it_span = it.deduction_span(cur_pos)
                for nit in more:
                    nit_span = nit.deduction_span(cur_pos)
                    if nit_span not in self.deduced_by:
                        self.deduced_by[nit_span] = it_span
            elif dot_sym == next_sym:
                # Scan: This item was waiting for this particular terminal symbol at this location, so it can proceed.
                nit = it.proceed()
                new.add(nit)
                nit_span = nit.deduction_span(cur_pos + 1)
                if nit_span not in self.deduced_by:
                    self.deduced_by[nit_span] = DeductionSpan(dot_sym, (cur_pos, cur_pos + 1))
            elif dot_sym not in self.grammar.terminals:
                # Predict: If `dot_sym` is non-terminal, then we need to expand the item further.
                more = set(
                    Item(GrammarPoint(dot_sym, rule, 0), cur_pos)
                    for rule in range(len(self.grammar.rules[dot_sym])))
                # Again, no input symbol was consumed, so these also belong to the current state.
                old.update(more)
        return old, new

    def feed(self, c: Terminal):
        """_Feed_ the parser one terminal symbol `c`, one that comes after all the symbols it had been
        fed so far. This generates additional states according to the Earley algorithm."""
        assert isinstance(c, Terminal), f'expected a Terminal, got {type(c)}'

        cid = self.grammar.terminal_symbol(c)  # the current terminal symbol's integer representation
        cur = len(self.chart) - 1  # the current location at the input
        cur_state = self.chart[cur]  # the items that need processing

        # First, process the states once to produce two groups of new items:
        # - `old` are the items that should be appended to `self.char[cur]`.
        #   These items are generated by predicting from or completing existing states.
        # - `new` are the items that should be appended to `self.char[cur+1]`.
        #   These items are generated by scanning existing states.
        old, new = self.process(cur, cur_state, cid)
        # Only the _newly_ generated items matter, because the others are already accounted for.
        old.difference_update(cur_state)
        # Append the `old` items to the current state.
        self.chart[cur].update(old)
        # But now we need to the newly generated items that still belong to the current state.
        # So, keep doing that until we do not see previously unseen item anymore.
        while len(old) != 0:
            more_old, more_new = self.process(cur, old, cid)
            old = more_old.difference(self.chart[cur])
            self.chart[cur].update(old)
            # And, keep accumulating all the `new` items for the next state.
            new.update(more_new)
        # Now, construct `self.char[cur+1]` from all the accumulated `new` items.
        # But, ignore a special symbol `\0` which we will use just to trigger
        # all the pending predictions and completions for the old states.
        # TODO: Can this be done better?
        if c != Terminal("\0"):
            self.chart.append(new)

    def trace_deduction(self, it: DeductionSpan) -> DeductionNode:
        beg, end = it.span
        node = DeductionNode(it, [])
        if type(it.point) is GrammarPoint:
            for dot in range(it.point.dot, 0, -1):
                pt = GrammarPoint(it.point.sym, it.point.rule, dot)
                t = DeductionSpan(pt, (beg, end))
                # print('|', t.fmt(self.grammar), 'for', it.fmt(self.grammar))
                by = self.deduced_by[t]
                # print('|\tby', by.fmt(self.grammar))
                if t != by:
                    c = self.trace_deduction(by)
                    node.children.append(c)
                end = by.span[0]
            node.children.reverse()
        return node

    def complete_items(self, at: Union[int, None] = None) -> List[DeductionSpan]:
        if at is None:
            at = len(self.chart) - 1  # the current location at the input
        return [c.deduction_span(at) for c in self.chart[at]
                if c.point.sym == self.grammar.symbols.inverse[NonTerminal("<start>")]
                and self.grammar.get_symbol_at_point(c.point) is None]
