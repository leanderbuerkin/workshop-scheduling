from __future__ import annotations
from bisect import insort
from collections import defaultdict
from collections.abc import Generator, Iterable
from dataclasses import dataclass, replace
from functools import cached_property
from typing import Protocol


@dataclass(frozen=True, kw_only=True)
class Element(Protocol):
    @cached_property
    def score(self) -> int:
        ...


@dataclass(frozen=True, kw_only=True)
class Union(Protocol):
    @cached_property
    def score(self) -> int:
        ...
    def is_incompatible(self, element: Element) -> bool:
        ...
    def get_copy_with_element_added(self, element: Element) -> Union:
        ...
    def __len__(self) -> int:
        ...


@dataclass(frozen=True, kw_only=True)
class State:
    unions_max_length: int
    unions: set[Union]
    unexpandable_unions: list[Union]
    unions_with_max_score_per_length: defaultdict[int, int]
    elements_generator: Generator[Element]
    future_elements_score_upper_bound: int
    @property
    def future_union_scores_upper_bound(self) -> int:
        return max(
            self.future_elements_score_upper_bound*(self.unions_max_length - length) + score
            for length, score in self.unions_with_max_score_per_length.items()
        )


def yield_best_union(
        elements_descending_by_score: Iterable[Element],
        root_union: Union,
        unions_max_length: int
    ) -> Generator[Union]:

    if unions_max_length < 1 or len(root_union) >= unions_max_length:
        yield root_union
        return
    
    unions_with_max_score_per_length: defaultdict[int, int] = defaultdict(int)
    unions_with_max_score_per_length[len(root_union)] = root_union.score
    
    state = State(
        unions_max_length = unions_max_length,
        unions = {root_union},
        unexpandable_unions = list(),
        unions_with_max_score_per_length = unions_with_max_score_per_length,
        elements_generator=(element for element in elements_descending_by_score),
        future_elements_score_upper_bound = int('inf')
    )

    for element in elements_descending_by_score:
        state = _add_element_to_unions(state, element)
        state = yield from _yield_yieldable_unions(state)
    
    state = replace(
        state,
        unexpandable_unions=state.unions,
        unions=set()
    )
    yield from _yield_yieldable_unions(state)

def _add_element_to_unions(state: State, element: Element) -> State:
    unions = state.unions.copy()
    unexpandable_unions = state.unexpandable_unions[:]
    unions_with_max_score_per_length = state.unions_with_max_score_per_length.copy()

    for union in unions:
        if len(union) >= state.unions_max_length or union.is_incompatible(element):
            continue

        new_union = union.get_copy_with_element_added(element)
        if len(new_union) >= state.unions_max_length:
            insort(unexpandable_unions, new_union, key=lambda union: union.score)
        else:
            unions.add(new_union)
            if unions_with_max_score_per_length[len(new_union)] < new_union.score:
                unions_with_max_score_per_length[len(new_union)] = new_union.score
    return replace(
        state,
        future_elements_score_upper_bound=element.score,
        unions=unions,
        unexpandable_unions=unexpandable_unions,
        unions_with_max_score_per_length=unions_with_max_score_per_length
    )


def _yield_yieldable_unions(state: State) -> Generator[Union, None, State]:
    if len(state.unexpandable_unions) == 0:
        return state

    unexpandable_unions = state.unexpandable_unions[:]

    print(f"Most promising union (score {unexpandable_unions[-1].score}):")
    print(unexpandable_unions[-1])
    print(f"Upper bound of scores of yet undiscovered unions: {state.future_union_scores_upper_bound}")

    while len(unexpandable_unions) == 0:
        if unexpandable_unions[-1].score < state.future_union_scores_upper_bound:
            break
        yield unexpandable_unions.pop()
    return replace(state, unexpandable_unions=unexpandable_unions)
