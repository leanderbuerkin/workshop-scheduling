
from bisect import insort
from collections.abc import Callable, Generator, Iterator
from functools import cached_property
from itertools import islice
from typing import Protocol, Self


class ElementProtocol(Protocol):
    @cached_property
    def score(self) -> int:
        ...
    def __lt__(self, other: Self) -> bool:
        ...


class UnionProtocol(ElementProtocol, Protocol):
    def __len__(self) -> int:
        ...


def yield_best_unions[Element: ElementProtocol, Union: UnionProtocol](
        elements_high_to_low: Iterator[Element],
        elements_per_union: int,
        root_union: Union,
        combine: Callable[[Union, Element], Union | None]
    ) -> Generator[Union]:

    elements: list[Element] = list()
    unfinished_unions: set[Union] = set()
    addable_element_index: dict[Union, int] = dict()
    completed_unions: list[Union] = list()

    def can_be_expanded(union: Union) -> bool:
        if len(elements) < addable_element_index[union]:
            raise Exception(
                f"This union maybe got an element added that was not in elements" +
                f" ({len(elements)} < {addable_element_index[union]}):\n{union}"
            )

        if len(elements) == addable_element_index[union]:
            elements.extend(islice(elements_high_to_low, 1))

        return len(elements) > addable_element_index[union]


    def add_union(union: Union, addable_element_index_of_union: int):
        if len(union) > elements_per_union:
            raise Exception(f"Union exceeded target length of {elements_per_union}: {union}")
        
        addable_element_index[union] = addable_element_index_of_union

        if len(union) < elements_per_union and can_be_expanded(union):
            unfinished_unions.add(union)
        else:
            addable_element_index.pop(union)
            insort(completed_unions, union)


    def get_score_upper_bound(union: Union) -> int:
        index = addable_element_index[union]
        missing_elements_count = max(0, elements_per_union - len(union))
        best_completion = elements[index : index + missing_elements_count]
        return union.score + sum(element.score for element in best_completion)


    add_union(root_union, 0)

    while len(unfinished_unions) > 0:
        most_promising_union = max(unfinished_unions, key=lambda union: get_score_upper_bound(union))
        unfinished_unions.remove(most_promising_union)

        yieldable_score_min = get_score_upper_bound(most_promising_union)
        while len(completed_unions) > 0 and completed_unions[-1].score >= yieldable_score_min:
            yield completed_unions.pop()

        element_index = addable_element_index[most_promising_union]
        addable_element = elements[element_index]
        if new_union := combine(most_promising_union, addable_element):
            add_union(new_union, element_index + 1)
        add_union(most_promising_union, element_index + 1)

    while len(completed_unions) > 0:
        yield completed_unions.pop()
