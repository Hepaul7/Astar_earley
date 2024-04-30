"""
The "fast" implementation of the Earley algorithm.
TODO: Some of the data types and methods are duplicated with the naive version. Perhaps it would be nicer to have a common interface.
"""

from dataclasses import dataclass
from typing import Set, List, Tuple, TypeAlias, Self, Union

from cfg import GrammarPoint, Grammar, StarPoint, Symbol
from node import NonTerminal, Terminal


@dataclass(frozen=True)
class Item:
    """An `Item` represents a partial parse of a grammar rule at some point in the input string."""
    point: Union[StarPoint, GrammarPoint]
    """This is can be a partially parsed (i.e. dotted) rule, like the naive version of Earley algorithm.
    But this can also be a partially parsed _star_ rule, introduced in the fast version of Earley algorithm."""
    beg: int
    """Where this parse began in the input string."""

    def proceed(self) -> Self:
        """Moves the `dot` of the item one step forward in the rule.
        PRE: `dot` must _not_ be at or past the end of the rule."""
        return Item(self.point.proceed(), self.beg)


State: TypeAlias = Set[Item]
"""A `State` is the set of all items (i.e. partially parsed rules) to be considered
for parsing the terminal symbol at a particular point in the input string."""
Chart: TypeAlias = List[State]
"""A `Chart` is the list of all the states for the input, with an extra state for the very
beginning of the string (i.e. the chart has a length of `n+1` where `n` is the input size)."""


@dataclass
class Earley:
    """Holds the logic to produce the various states while parsing an input string
    in a particular grammar with the Earley algorithm."""
    grammar: Grammar
    chart: Chart

    def __init__(self, g: Grammar):
        self.grammar = g
        self.chart = [set()]
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
            assert type(it.point) in {StarPoint, GrammarPoint}
            if type(it.point) is GrammarPoint:
                dot_sym = self.grammar.get_symbol_at_point(it.point)  # the symbol right after the `dot`.
                if dot_sym is None:
                    # Complete Star: If there is no symbol after the `dot`, we have completed this item.
                    # TODO: optimise here by tracking?

                    # Find any other _star_ items that waiting at this item's start position for this item's
                    # generating symbol. Those items can now move forward one step now.
                    # We care only about star items here, because predictions always go through a star item now,
                    # unlike the naive Earley algorithm.
                    more = set(
                        cit.proceed() for cit in self.chart[it.beg]
                        if type(cit.point) is StarPoint
                        and not cit.point.done
                        and cit.point.sym == it.point.sym)
                    # But these items still belongs to the current state, since no input symbol was consumed here.
                    old.update(more)
                elif dot_sym == next_sym:
                    # Scan: This item was waiting for this particular terminal symbol at this location, so it can
                    # proceed.
                    new.add(it.proceed())
                elif dot_sym not in self.grammar.terminals:
                    # Predict Star: If `dot_sym` is non-terminal, then we need to expand the item further. But in this
                    # version, we always expand to a star item first.
                    # Again, no input symbol was consumed, so these also belong to the current state.
                    old.add(Item(StarPoint(dot_sym, False), cur_pos))
            elif type(it.point) is StarPoint:
                assert it.point.sym not in self.grammar.terminals
                if it.point.done:
                    # Complete: This star item was complete. So, now we find any other items that _waiting_ at this
                    # item's start position for this item's generating symbol. Those items can now move forward one
                    # step now.
                    # TODO: optimise here by tracking?
                    more = set(
                        cit.proceed() for cit in self.chart[it.beg]
                        if type(cit.point) is GrammarPoint
                        and self.grammar.get_symbol_at_point(cit.point) == it.point.sym)
                    # Again, no input symbol was consumed, so these also belong to the current state.
                    old.update(more)
                else:
                    # Predict: Expand the star item into a proper partial-parse item.
                    more = set(
                        Item(GrammarPoint(it.point.sym, rule, 0), cur_pos)
                        for rule in range(len(self.grammar.rules[it.point.sym])))
                    # Again, no input symbol was consumed, so these also belong to the current state.
                    old.update(more)
        return old, new

    def feed(self, c: Terminal):
        """_Feed_ the parser one terminal symbol `c`, one that comes after all the symbols it had been
        fed so far. This generates additional states according to the Earley algorithm."""

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
