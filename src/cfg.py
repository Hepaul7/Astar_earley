"""
We keep the representation of various objects related to the context-free grammar (CFG) here.
"""

from dataclasses import dataclass, field
from typing import Set, List, Tuple, Union, TypeAlias, Self, Optional

from bidict import bidict

from node import Node, NonTerminal, Terminal

Symbol: TypeAlias = int
"""A `Symbol` represents a terminal or non-terminal symbol in the grammar.
It is an integer type for performance reasons."""
Rule: TypeAlias = List[Symbol]
"""A `Rule` represents a right hand side of a production rule in the grammar.
So the entire rule is represented by a `Symbol` and a `Rule`."""
AltRules: TypeAlias = List[Rule]
"""An `AltRule` represents alternative production rules from the same symbol (i.e. piped rules)."""


@dataclass(frozen=True)
class GrammarPoint:
    """A `GrammarPoint` represents a partially parsed production rule,
    i.e. a rule with a dot that can be anywhere in the sequence."""
    sym: Symbol
    rule: int
    dot: int

    def proceed(self) -> Self:
        """Moves the dot one step forward in the rule.
        PRE: `dot` must _not_ be at or past the end of the rule."""
        return GrammarPoint(self.sym, self.rule, self.dot + 1)


@dataclass(frozen=True)
class StarPoint:
    """A `StarPoint` represents a symbol to be parsed with any of its alternative production rules (i.e. a star item).
    Since a star item only has a length one until it's complete, its `dot` is just a boolean value."""
    sym: Symbol
    done: bool

    def proceed(self) -> Self:
        """Moves the dot one step forward in the rule, i.e. essentially completing the item.
        PRE: `dot` must be False."""
        assert not self.done
        return StarPoint(self.sym, True)


@dataclass
class Grammar:
    """A `Grammar` represents the entire description of a context free grammar,
    keeping track of its symbols and rules."""

    symbols: bidict[Symbol, Node] = field(default_factory=bidict)
    """A bijective map matching a `Symbol` to its string representation."""
    terminals: Set[Symbol] = field(default_factory=set)
    """A set of all terminal symbols."""
    rules: List[AltRules] = field(default_factory=list)
    """A list of rules where i-th entry contains all the production rules
    for the symbol represented by the integer `i`."""

    def __init__(self):
        self.symbols = bidict()
        self.terminals = set()
        self.rules = []
        self.add_symbol(NonTerminal("<start>"), False).add_symbol(Terminal("\0"), True)

    def add_symbol(self, sym: Node, terminal: bool) -> Self:
        """Register a terminal or non-terminal symbol to the grammar."""
        # We can remove the terminal parameter now, but I don't want to modify the function signature yet.
        assert len(sym.symbol()) > 0, "symbol cannot be empty!"
        sym_id = len(self.symbols)
        if isinstance(sym, Terminal):
            assert sym_id >= len(self.rules) or len(self.rules[sym_id]) == 0, \
                f"error adding a terminal symbol `{sym}`: a production rule exists for it"
        self.symbols[sym_id] = sym
        if isinstance(sym, Terminal):
            self.terminals.add(sym_id)
        return self

    def convert_rule(self, rule: Tuple[Node, List[Node]]) -> Tuple[Symbol, Rule]:
        """Given a rule represented using the string representations of its symbols,
        produce its integer representation."""
        sym, parts = rule
        sym_id = self.symbols.inverse[sym]
        assert sym_id is not None, f"`{sym}` does not exist in the grammar"
        assert sym_id not in self.terminals, \
            f"`{sym}` is a terminal symbol in the grammar, so production rules on it are not allowed"
        part_ids = []
        for p in parts:
            p_id = self.symbols.inverse[p]
            assert p_id is not None, f"`{sym}` does not exist in the grammar"
            part_ids.append(p_id)
        return sym_id, part_ids

    def add_rule(self, r: Tuple[Node, List[Node]]) -> Self:
        """Add a single production rule, provided its string representation, to the grammar."""
        sym_id, rule = self.convert_rule(r)
        if sym_id >= len(self.rules):
            self.rules.extend([[] for _ in range(len(self.symbols) - len(self.rules))])
        self.rules[sym_id].append(rule)
        return self

    def get_symbol_at_point(self, pt: GrammarPoint) -> Union[Symbol, None]:
        """Given a `GrammarPoint`, find the symbol right after the `dot`."""
        rule = self.rules[pt.sym][pt.rule]
        return rule[pt.dot] if pt.dot < len(rule) else None

    def terminal_symbol(self, c: Terminal) -> Symbol:
        """Given a terminal symbol `c` in its string representation, find the integer representation of it."""
        assert c in self.symbols.inverse and self.symbols.inverse[c] in self.terminals
        return self.symbols.inverse[c]

    # A bunch of pretty-printing helpers follows.

    def fmt_rules_for(self, sym: Symbol) -> str:
        sym_str = self.symbols[sym].symbol()
        assert sym_str is not None, f"{sym} is not a valid symbol in the grammar"
        if sym >= len(self.rules) or len(self.rules[sym]) == 0:
            return ""
        return f"{sym_str} → {'|'.join([''.join([self.symbols[p].symbol() for p in r]) for r in self.rules[sym]])}"

    def fmt_all_rules(self) -> List[str]:
        return [x for x in [self.fmt_rules_for(sym) for sym in range(len(self.rules))] if x]

    def fmt_all_symbols(self) -> List[str]:
        return [f"{sym.symbol()}{'*' if symid in self.terminals else ''}" for symid, sym in self.symbols.items()]

    def fmt_point(self, pt: Union[GrammarPoint, StarPoint], sep: Optional[str] = None) -> str:
        sep = sep if sep is not None else ''
        if type(pt) is GrammarPoint:
            assert pt.sym < len(self.rules), f"moral panic: no rule with a symbol {pt.sym} for item {pt}!"
            assert pt.rule < len(self.rules[pt.sym]), f"moral panic: no {pt.rule}-th rule for item {pt}!"
            assert pt.sym in self.symbols, f"moral panic: {pt.sym} is not a valid symbol for item {pt}"
            sym = self.symbols[pt.sym].symbol()
            rule = self.rules[pt.sym][pt.rule]
            assert pt.dot <= len(
                rule), f"moral panic: rule's length is only {len(rule)}, dot is at {pt.dot} for item {pt}!"
            parts = [self.symbols[p].symbol() for p in rule]
            head, tail = parts[:pt.dot], parts[pt.dot:]
            return f"{sym} → {''.join(head)}•{sep.join(tail)}"
        else:
            assert pt.sym in self.symbols, f"moral panic: {pt.sym} is not a valid symbol for item {pt}"
            sym = self.symbols[pt.sym].symbol()
            return f"{sym} → ★•" if pt.done else f"{sym} → •★"
