from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
from types import MappingProxyType

frozendict = MappingProxyType


@dataclass(frozen=True, slots=True, kw_only=True)
class Workshop:
    index: int
    name: str
    participants: frozenset[str]
    @property
    def score(self) -> int:
        return len(self.participants)


@dataclass(frozen=True, slots=True, kw_only=True)
class TimeSlot:
    workshops: frozenset[Workshop]
    addable_workshops: frozenset[Workshop]
    workshops_count_target: int

    @property
    def missing_workshops_count(self) -> int:
        return self.workshops_count_target - len(self.workshops)
    @property
    def is_full(self) -> bool:
        if len(self.workshops) > self.workshops_count_target:
            raise Exception(
                f"This time slot has more workshops than it is allowed to have: " +
                f"{len(self.workshops)} > {self.workshops_count_target}\n" +
                f"Workshops: {self.workshops}"
            )
        return self.missing_workshops_count == 0

    @property
    def participants(self) -> frozendict[str, int]:
        return frozendict(Counter(
            participant
            for workshop in self.workshops
            for participant in workshop.participants
        ))
    @property
    def participants_with_exactly_one_option(self) -> frozenset[str]:
        return frozenset(filter(lambda key: self.participants[key] == 1, self.participants.keys()))
    @property
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

    @property
    def score_upper_bound(self) -> int:
        best_completion = sorted(
            self.addable_workshops,
            key=lambda workshop: workshop.score,
            reverse=True
        )[:self.missing_workshops_count]
        return self.score + sum(workshop.score for workshop in best_completion)
    @property
    def expandable(self) -> bool:
        return not(self.is_full) and len(self.addable_workshops) > 0
    @property
    def expansions(self) -> frozenset[TimeSlot]:
        if not self.expandable:
            raise Exception("Check Expandability with .expandable before expansion.")
        expanding_workshops = sorted(
            self.addable_workshops,
            key=lambda workshop: workshop.score
        )
        new_time_slots = {TimeSlot(
            workshops=self.workshops,
            addable_workshops=frozenset(),
            workshops_count_target=self.workshops_count_target
        )}
        while len(expanding_workshops) > 0:
            expanding_workshop = expanding_workshops.pop()
            new_time_slots.add(TimeSlot(
                workshops=frozenset(self.workshops | {expanding_workshop}),
                addable_workshops=frozenset(expanding_workshops),
                workshops_count_target=self.workshops_count_target
            ))
        return frozenset(new_time_slots)

    def contains(self, workshop: Workshop) -> bool:
        return workshop in self.workshops

    def __str__(self) -> str:
        output = f"Score {self.score}: "
        output += ", ".join(
            f"[{workshop}]"
            for workshop in sorted(self.workshops, key=lambda w: w.score, reverse=True)
        )
        return output


@dataclass(frozen=True, slots=True, kw_only=True)
class TimeTable:
    time_slots: frozenset[TimeSlot]
    addable_time_slots: frozenset[TimeSlot]
    time_slots_count_target: int

    @property
    def missing_time_slots_count(self) -> int:
        return self.time_slots_count_target - len(self.time_slots)
    @property
    def is_full(self) -> bool:
        if len(self.time_slots) > self.time_slots_count_target:
            raise Exception(
                f"This time slot has more workshops than it is allowed to have: " +
                f"{len(self.time_slots)} > {self.time_slots_count_target}\n" +
                f"Workshops: {self.time_slots}"
            )
        return self.missing_time_slots_count == 0

    @property
    def needs_time_slots(self) -> bool:
        return self.needs_time_slots_to_estimate_score or self.needs_time_slots_to_expand
    @property
    def needs_time_slots_to_expand(self) -> bool:
        return not(self.is_full) and len(self.addable_time_slots) == 0
    @property
    def needs_time_slots_to_estimate_score(self) -> bool:
        return len(self.addable_time_slots) - self.missing_time_slots_count < 0

    @property
    def score(self) -> int:
        return sum(time_slot.score for time_slot in self.time_slots)
    @property
    def score_upper_bound(self) -> int:
        if self.needs_time_slots_to_estimate_score:
            raise Exception("Add addable time slots before estimating the score.")
        best_completion = sorted(
            self.addable_time_slots,
            key=lambda time_slot: time_slot.score,
            reverse=True
        )[:self.missing_time_slots_count]
        return self.score + sum(time_slot.score for time_slot in best_completion)
    @property
    def expandable(self) -> bool:
        return not(self.is_full) and len(self.addable_time_slots) > 0
    @property
    def expansions(self) -> frozenset[TimeTable]:
        if not self.expandable:
            raise Exception("Check Expandability with .expandable before expansion.")
        expanding_time_slots = sorted(
            self.addable_time_slots,
            key=lambda time_slot: time_slot.score
        )
        new_time_tables = {TimeTable(
            time_slots=self.time_slots,
            addable_time_slots=frozenset(),
            time_slots_count_target=self.time_slots_count_target
        )}
        while len(expanding_time_slots) > 0:
            expanding_time_slot = expanding_time_slots.pop()
            new_time_tables.add(TimeTable(
                time_slots=frozenset(self.time_slots | {expanding_time_slot}),
                addable_time_slots=frozenset(expanding_time_slots),
                time_slots_count_target=self.time_slots_count_target
            ))
        return frozenset(new_time_tables)

    def contains(self, workshop: Workshop) -> bool:
        return any(time_slot.contains(workshop) for time_slot in self.time_slots)

    def __str__(self) -> str:
        output = f"Time table with score {self.score}:"
        for time_slot in sorted(self.time_slots, key=lambda s: s.score, reverse=True):
            output += f"\n  {time_slot}"
        return output
