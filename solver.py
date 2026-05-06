
from bisect import insort
from collections.abc import Callable, Generator
from itertools import islice

from data_structures import Scored, SizedScored

def yield_best_unions[Element: Scored, Union: SizedScored](
        elements_high_to_low: Generator[Element],
        elements_per_union: int,
        root_union: Union,
        combine: Callable[[Union, Element], Union | None]
    ) -> Generator[Union]:

    elements: list[Element] = list()
    expandable_unions: list[Union] = list()
    score_upper_bounds: dict[Union, int] = dict()
    addable_element_indizes: dict[Union, int] = dict()
    completed_unions: list[Union] = list()

    def get_score_upper_bound(union: Union) -> int:
        index = addable_element_indizes[union]
        missing_elements_count = max(0, elements_per_union - len(union))
        elements.extend(islice(elements_high_to_low, max(0, index + missing_elements_count - len(elements))))
        best_completion = elements[index : index + missing_elements_count]
        return union.score + sum(element.score for element in best_completion)

    def can_be_expanded(union: Union) -> bool:
        index = addable_element_indizes[union]
        if len(elements) < index:
            raise ValueError(
                f"This union maybe got an element added that was not in elements" +
                f" ({len(elements)} < {index}):\n{union}"
            )
        elements.extend(islice(elements_high_to_low, max(0, index + 1 - len(elements))))
        return len(elements) > index

    def add_union(union: Union):
        if len(union) > elements_per_union:
            raise Exception(f"Union exceeded target length of {elements_per_union}: {union}")

        if union not in addable_element_indizes.keys():
            addable_element_indizes[union] = 0
        if len(union) < elements_per_union and can_be_expanded(union):
            score_upper_bounds[union] = get_score_upper_bound(union)
            insort(
                expandable_unions, union,
                key=lambda union: (score_upper_bounds[union], addable_element_indizes[union])
            )
        else:
            del addable_element_indizes[union]
            if union in score_upper_bounds:
                del score_upper_bounds[union]
            insort(completed_unions, union, key=lambda union: (union.score, -len(union)))


    add_union(root_union)
    while len(expandable_unions) > 0:
        most_promising_union = expandable_unions.pop()

        yieldable_score_min = score_upper_bounds[most_promising_union]
        while len(completed_unions) > 0 and completed_unions[-1].score >= yieldable_score_min:
            yield completed_unions.pop()

        index = addable_element_indizes[most_promising_union]
        addable_element_indizes[most_promising_union] += 1
        new_element = elements[index]
        if new_union := combine(most_promising_union, new_element):
            addable_element_indizes[new_union] = addable_element_indizes[most_promising_union]
            add_union(new_union)
        add_union(most_promising_union)

    while len(completed_unions) > 0:
        yield completed_unions.pop()