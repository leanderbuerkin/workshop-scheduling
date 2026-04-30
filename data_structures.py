from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
from functools import cached_property, total_ordering
from types import MappingProxyType

frozendict = MappingProxyType


@total_ordering
@dataclass(frozen=True, kw_only=True)
class Workshop:
    index: int
    name: str
    participants: frozenset[str]
    @cached_property
    def score(self) -> int:
        return len(self.participants)

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Workshop):
            raise TypeError
        return self.score < other.score

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Workshop) and self.score == other.score

    def __str__(self) -> str:
        return f"{self.name} (score {self.score}): {", ".join(sorted(self.participants, key=lambda p: int(p)))}"


@total_ordering
@dataclass(frozen=True, kw_only=True)
class TimeSlot:
    workshops: frozenset[Workshop]

    @cached_property
    def participants(self) -> frozendict[str, int]:
        return frozendict(Counter(
            participant
            for workshop in self.workshops
            for participant in workshop.participants
        ))

    @cached_property
    def participants_with_exactly_one_option(self) -> frozenset[str]:
        return frozenset(p for p, options_count in self.participants.items() if options_count == 1)

    @cached_property
    def score(self) -> int:
        """
        There are the following options:
        - Number of participants that are interested in at least one workshop in this time slot
        - Number of participants that are interested in exactly  one workshop in this time slot

        The first option interprets the participants input more like
        "I find it important that this workshop takes place" and less like "I want to participate in this workshop".
        The result should be a tight time table
        where participants often have to choose between multiple workshops they like
        and every slot is full since there is no penalty for having multiple workshops at once.

        The second option returns only those workshops where a lot of people are interested
        and those workshop, where the participants submitted very little wishes (e.g. a special interest group).
        This option is considered a bit better,
        since only workshops take place, where it is "really worth it" - as far as the program can tell.
        """
        score = len(self.participants_with_exactly_one_option)
        if score > sum(workshop.score for workshop in self.workshops):
            raise Exception(
                "The score of this timeslot is bigger then the scores of its workshops combined.\n" +
                "Since the scores of the workshops combined are used as an optimistic heuristic they must be an upper bound." 
            )
        return score

    def is_compatible(self, element: Workshop) -> bool:
        return element in self.workshops

    def copy_and_expand_copy(self, element_to_expand_with: Workshop) -> TimeSlot:
        return TimeSlot(workshops=frozenset(self.workshops | {element_to_expand_with}))

    def __len__(self) -> int:
        return len(self.workshops)

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Workshop):
            raise TypeError
        return self.score < other.score

    def __eq__(self, other: object) -> bool:
        return isinstance(other, TimeSlot) and self.score == other.score

    def __str__(self) -> str:
        output = f"Score {self.score}: "
        output += ", ".join(
            f"[{", ".join(sorted(workshop.participants, key=lambda p: int(p)))}]"
            for workshop in sorted(self.workshops, key=lambda w: w.score, reverse=True)
        )
        return output


@total_ordering
@dataclass(frozen=True, kw_only=True)
class TimeTable:
    time_slots: frozenset[TimeSlot]
    @cached_property
    def score(self) -> int:
        return sum(time_slot.score for time_slot in self.time_slots)

    def is_compatible(self, element: TimeSlot) -> bool:
       return all(
            not workshop in element.workshops
            for time_slot in self.time_slots
            for workshop in time_slot.workshops
        )

    def copy_and_expand_copy(self, element_to_expand_with: TimeSlot) -> TimeTable:
        return TimeTable(time_slots=frozenset(self.time_slots | {element_to_expand_with}))

    def __len__(self) -> int:
        return len(self.time_slots)

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, TimeTable):
            raise TypeError
        return self.score < other.score

    def __eq__(self, other: object) -> bool:
        return isinstance(other, TimeTable) and self.score == other.score

    def __str__(self) -> str:
        output = f"Time table with score {self.score}:"
        for time_slot in sorted(self.time_slots, key=lambda s: s.score, reverse=True):
            output += f"\n  {time_slot}"
        return output
