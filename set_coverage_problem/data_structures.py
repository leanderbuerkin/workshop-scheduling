from __future__ import annotations
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True, kw_only=True)
class Union:
    sets: frozenset[frozenset[Any]]
    expanding_sets: frozenset[frozenset[Any]]
    operands_count_upper_bound: int
    @property
    def can_be_expanded(self) -> bool:
        return self.addable_sets_count > 0

    @property
    def addable_sets_count(self) -> int:
        if len(self.sets) > self.operands_count_upper_bound:
            raise Exception(
                f"This union has more sets than it is allowed to: " +
                f"{len(self.sets)} > {self.operands_count_upper_bound}\n" +
                f"Sets: {self.sets}"
            )
        if len(self.expanding_sets) < self.operands_count_upper_bound - len(self.sets):
            return len(self.expanding_sets)
        else:
            return self.operands_count_upper_bound - len(self.sets)

    @property
    def current_size(self) -> int:
        empty_set: set[Any] = set()
        return len(empty_set.union(self.sets))

    @property
    def size_upper_bound(self) -> int:
        best_possible_completion = sorted(
            self.expanding_sets,
            key=lambda _set: len(_set),
            reverse=True
        )[:self.addable_sets_count]
        best_union = self.sets | frozenset(best_possible_completion)
        return sum(len(_set) for _set in best_union)

    @property
    def expansions(self) -> set[Union]:
        if not self.can_be_expanded:
            return set()
        new_sets = sorted(
            self.expanding_sets,
            key=lambda _set: len(_set)
        )
        new_unions = {Union(
            sets=self.sets,
            expanding_sets=frozenset(),
            operands_count_upper_bound=self.operands_count_upper_bound
        )}
        while len(new_sets) > 0:
            new_set = new_sets.pop()
            new_unions.add(Union(
                sets=frozenset(self.sets | frozenset(new_set)),
                expanding_sets=frozenset(new_sets),
                operands_count_upper_bound=self.operands_count_upper_bound
            ))
        return new_unions
