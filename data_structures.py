from bisect import insort
from collections.abc import Callable, Generator, Iterator
from dataclasses import dataclass
from itertools import islice


# todo: Combine function
# todo: score functions
# todo: Workshops scores/categories from People instead of in/out

@dataclass(frozen=True, order=True, kw_only=True)
class ScoredHashable:
    score: int


@dataclass(frozen=True, order=True, kw_only=True)
class ScoredHashableWithLength(ScoredHashable):
    def __len__(self) -> int:
        raise NotImplementedError("__len__() must be implemented!")


@dataclass(frozen=True, kw_only=True)
class Workshop(ScoredHashable):
    index: int
    name: str
    participants: frozenset[str]

    def __str__(self) -> str:
        return f"{self.name} (score {self.score}): {", ".join(sorted(self.participants))}"


@dataclass(frozen=True, kw_only=True)
class TimeSlot(ScoredHashableWithLength):
    workshops: frozenset[Workshop]

    def __len__(self) -> int:
        return len(self.workshops)

    def __str__(self) -> str:
        output = f"Score {self.score}: "
        output += ", ".join(f"[{workshop}]" for workshop in sorted(self.workshops, reverse=True))
        return output


@dataclass(frozen=True, kw_only=True)
class TimeTable(ScoredHashableWithLength):
    time_slots: frozenset[TimeSlot]

    def __len__(self) -> int:
        return len(self.time_slots)

    def __str__(self) -> str:
        output = f"\nTimeTable (score {self.score})"
        output += "\n  ".join(str(time_slot) for time_slot in self.time_slots)
        return output + "\n"


def yield_best_unions[Element: ScoredHashable, Union: ScoredHashableWithLength](
        elements_high_to_low: Iterator[Element],
        elements_per_union: int,
        root_union: Union,
        combine: Callable[[Union, Element], Union | None]
    ) -> Generator[Union]:

    @dataclass(order=True, kw_only=True)
    class ExpandableUnion:
        score_upper_bound: int # first for automatic ordering
        union: Union
        addable_element_index: int

        def __len__(self) -> int:
            return len(self.union)


    elements: list[Element] = list()
    expandable_unions: list[ExpandableUnion] = list()
    completed_unions: list[Union] = list()


    def get_unfinished_union(union: Union, addable_element_index: int) -> ExpandableUnion:
        missing_elements_count = max(0, elements_per_union - len(union))
        best_completion = elements[addable_element_index : addable_element_index + missing_elements_count]

        return ExpandableUnion(
            score_upper_bound=union.score + sum(element.score for element in best_completion),
            union=union,
            addable_element_index=addable_element_index
        )


    def can_be_expanded(addable_element_index: int) -> bool:
        if len(elements) < addable_element_index:
            raise ValueError(
                f"This union maybe got an element added that was not in elements" +
                f" {len(elements)} < {addable_element_index}"
            )
        return len(elements) > addable_element_index


    def add_union(union: Union, addable_element_index: int):
        if len(union) > elements_per_union:
            raise Exception(f"Union exceeded target length of {elements_per_union}: {union}")

        missing_elements_count = max(1, elements_per_union - len(union))  # at least one is needed in can_be_expanded()
        elements.extend(islice(elements_high_to_low, addable_element_index + missing_elements_count - len(elements)))

        if len(union) < elements_per_union and can_be_expanded(addable_element_index):
            insort(expandable_unions, get_unfinished_union(union, addable_element_index))
        else:
            insort(completed_unions, union)


    add_union(root_union, 0)

    while len(expandable_unions) > 0:
        most_promising_union = expandable_unions.pop()

        yieldable_score_min = most_promising_union.score_upper_bound
        while len(completed_unions) > 0 and completed_unions[-1].score >= yieldable_score_min:
            yield completed_unions.pop()

        addable_element = elements[most_promising_union.addable_element_index]
        if new_union := combine(most_promising_union.union, addable_element):
            add_union(new_union, most_promising_union.addable_element_index + 1)
        add_union(most_promising_union.union, most_promising_union.addable_element_index + 1)

    while len(completed_unions) > 0:
        yield completed_unions.pop()
