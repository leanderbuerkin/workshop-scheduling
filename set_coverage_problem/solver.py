from collections.abc import Generator, Iterable
from typing import Any

from set_coverage_problem.data_structures import Union


class SetCoverageSolver:
    unbeatable_unions: list[Union]
    _unfinished_unions: set[Union]
    _finished_unions: set[Union]

    def __init__(self, sets: Iterable[set[Any] | frozenset[Any]], operands_count_upper_bound: int):
        self._unfinished_unions = set()
        self._finished_unions = set()
        self.unbeatable_unions = list()
        self._add_new_union(Union(
            sets=frozenset(),
            expanding_sets=frozenset(frozenset(_set) for _set in sets),
            operands_count_upper_bound=operands_count_upper_bound
        ))

    def yield_best_unions(self) -> Generator[Union]:
        self._finished_unions |= set(self.unbeatable_unions)
        self.unbeatable_unions = list()
        while len(self._unfinished_unions) > 0:
            for union in self._yield_currently_best_unions():
                yield union
            most_promising_union = max(
                self._unfinished_unions,
                key=lambda union: union.size_upper_bound
            )
            self._unfinished_unions.remove(most_promising_union)
            self._add_new_unions(most_promising_union.expansions)

    def _yield_currently_best_unions(self) -> Generator[Union]:
        undiscovered_unions_size_upper_bound = max(
            union.size_upper_bound
            for union in self._unfinished_unions
        )
        for union in sorted(self._finished_unions, key=lambda union: union.current_size):
            if union.current_size > undiscovered_unions_size_upper_bound:
                self._finished_unions.remove(union)
                self.unbeatable_unions.append(union)
                yield union
            else:
                break

    def _add_new_unions(self, new_unions: Iterable[Union]):
        for new_union in new_unions:
            self._add_new_union(new_union)
    
    def _add_new_union(self, new_union: Union):
        if new_union.can_be_expanded:
            self._unfinished_unions.add(new_union)
        else:
            self._finished_unions.add(new_union)
