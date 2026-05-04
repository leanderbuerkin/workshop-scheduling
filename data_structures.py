
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

    def __lt__(self, other: Workshop) -> bool:
        return self.score < other.score

    def __str__(self) -> str:
        return f"{self.name} (score {self.score}): {", ".join(sorted(self.participants))}"


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
        score = len(self.participants_with_exactly_one_option)
        self._raise_exception_if_score_is_invalid(score)
        return score

    @cached_property
    def _highest_allowed_score(self) -> int:
        return sum(workshop.score for workshop in self.workshops)

    def _raise_exception_if_score_is_invalid(self, score: int):
        if score > self._highest_allowed_score:
            raise Exception(
                "The score of this time slot is bigger then the scores of its workshops combined.\n" +
                "Since the scores of the workshops combined are used as an optimistic heuristic they must be an upper bound." +
                f"{score} > {self._highest_allowed_score}\n{self}"
            )
        if score < 0:
            raise Exception(f"The score must always be positive: {score}\n{self}")

    def __lt__(self, other: TimeSlot) -> bool:
        return self.score < other.score

    def __len__(self) -> int:
        return len(self.workshops)

    def __str__(self) -> str:
        output = f"Score {self.score}: "
        output += ", ".join(f"[{workshop}]" for workshop in sorted(self.workshops, reverse=True))
        return output


@dataclass(frozen=True, kw_only=True)
class TimeTable:
    time_slots: frozenset[TimeSlot]

    @cached_property
    def score(self) -> int:
        score = sum(time_slot.score for time_slot in self.time_slots)
        self._raise_exception_if_score_is_invalid(score)
        return score

    @cached_property
    def _highest_allowed_score(self) -> int:
        return sum(time_slot.score for time_slot in self.time_slots)

    def _raise_exception_if_score_is_invalid(self, score: int):
        if score > self._highest_allowed_score:
            raise Exception(
                "The score of this time table is bigger then the scores of its time slots combined.\n" +
                "Since the scores of the time slots combined are used as an optimistic heuristic they must be an upper bound." +
                f"{score} > {self._highest_allowed_score}\n{self}"
            )
        if score < 0:
            raise Exception(f"The score must always be positive: {score}\n{self}")
 
    def __lt__(self, other: TimeTable) -> bool:
        return self.score < other.score

    def __len__(self) -> int:
        return len(self.time_slots)

    def __str__(self) -> str:
        output = f"\nTimeTable (score {self.score})"
        output += "\n  ".join(str(time_slot) for time_slot in self.time_slots)
        return output + "\n"
