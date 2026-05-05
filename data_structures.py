from bisect import insort
from collections.abc import Callable, Generator, Iterator
from dataclasses import dataclass
from itertools import islice

@dataclass(frozen=True, order=True, kw_only=True)
class ScoredHashable:
    score: int


@dataclass(frozen=True, order=True, kw_only=True)
class ScoredHashableWithLength(ScoredHashable):
    def __len__(self) -> int:
        raise Exception("Not implemented!")


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



# todo: score upper bound should be a post init



def yield_best_unions[Element: ScoredHashable, Union: ScoredHashableWithLength](
        elements_high_to_low: Iterator[Element],
        elements_per_union: int,
        root_union: Union,
        combine: Callable[[Union, Element], Union | None]
    ) -> Generator[Union]:


    @dataclass(order=True, kw_only=True)
    class UnfinishedUnion:
        score_upper_bound: int
        union: Union
        addable_element_index: int
        def __len__(self) -> int:
            return len(self.union)


    elements: list[Element] = list()
    unfinished_unions: list[UnfinishedUnion] = list()
    completed_unions: list[Union] = list()


    def can_be_expanded(union: UnfinishedUnion) -> bool:
        if len(elements) < union.addable_element_index:
            raise Exception(
                f"This union maybe got an element added that was not in elements" +
                f" ({len(elements)} < {union.addable_element_index}):\n{union}"
            )

        if len(elements) == union.addable_element_index:
            elements.extend(islice(elements_high_to_low, 1))

        return len(elements) > union.addable_element_index


    def add_union(union: UnfinishedUnion):
        if len(union) > elements_per_union:
            raise Exception(f"Union exceeded target length of {elements_per_union}: {union}")

        if len(union) < elements_per_union and can_be_expanded(union):
            insort(unfinished_unions, union)
        else:
            insort(completed_unions, union.union)


    def get_score_upper_bound(union: Union, addable_element_index: int) -> int:
        missing_elements_count = max(0, elements_per_union - len(union))
        best_completion = elements[addable_element_index : addable_element_index + missing_elements_count]
        return union.score + sum(element.score for element in best_completion)


    add_union(UnfinishedUnion(
        score_upper_bound=get_score_upper_bound(root_union, 0),
        union=root_union,
        addable_element_index=0
    ))

    while len(unfinished_unions) > 0:
        most_promising_union = unfinished_unions.pop()

        yieldable_score_min = most_promising_union.score_upper_bound
        while len(completed_unions) > 0 and completed_unions[-1].score >= yieldable_score_min:
            yield completed_unions.pop()

        addable_element = elements[most_promising_union.addable_element_index]
        if new_union := combine(most_promising_union.union, addable_element):
            add_union(UnfinishedUnion(
                score_upper_bound=most_promising_union.score_upper_bound,
                union=new_union,
                addable_element_index=most_promising_union.addable_element_index + 1
            ))
        add_union(UnfinishedUnion(
            score_upper_bound=get_score_upper_bound(most_promising_union.union, most_promising_union.addable_element_index + 1),
            union=most_promising_union.union,
            addable_element_index=most_promising_union.addable_element_index + 1
        ))

    while len(completed_unions) > 0:
        yield completed_unions.pop()
