from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
from functools import cached_property
from types import MappingProxyType

frozendict = MappingProxyType

@dataclass(frozen=True, kw_only=True)
class Workshop:
    index: int
    name: str
    participants: frozenset[str]
    @cached_property
    def score(self) -> int:
        return len(self.participants)
    def __str__(self) -> str:
        return f"{self.name} (score {self.score}): {", ".join(sorted(self.participants, key=lambda p: int(p)))}"


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
        return frozenset(filter(lambda key: self.participants[key] == 1, self.participants.keys()))
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

    def is_incompatible(self, workshop: Workshop) -> bool:
        return workshop in self.workshops

    def get_copy_with_element_added(self, workshop: Workshop) -> TimeSlot:
        return TimeSlot(workshops=frozenset(self.workshops | {workshop}))

    def __len__(self) -> int:
        return len(self.workshops)

    def __str__(self) -> str:
        output = f"Score {self.score}: "
        output += ", ".join(
            f"[{", ".join(sorted(workshop.participants, key=lambda p: int(p)))}]"
            for workshop in sorted(self.workshops, key=lambda w: w.score, reverse=True)
        )
        return output


@dataclass(frozen=True, kw_only=True)
class TimeTable:
    time_slots: frozenset[TimeSlot]
    @cached_property
    def score(self) -> int:
        return sum(time_slot.score for time_slot in self.time_slots)

    def is_incompatible(self, time_slot: TimeSlot) -> bool:
        return any(
            workshop in time_slot.workshops
            for time_slot in self.time_slots
            for workshop in time_slot.workshops
        )

    def get_copy_with_element_added(self, time_slot: TimeSlot) -> TimeTable:
        return TimeTable(time_slots=frozenset(self.time_slots | {time_slot}))

    def __len__(self) -> int:
        return len(self.time_slots)

    def __str__(self) -> str:
        output = f"Time table with score {self.score}:"
        for time_slot in sorted(self.time_slots, key=lambda s: s.score, reverse=True):
            output += f"\n  {time_slot}"
        return output
