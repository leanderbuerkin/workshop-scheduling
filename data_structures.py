
from dataclasses import dataclass
from functools import cached_property

type WorkshopIndex = int

@dataclass(frozen=True, order=True)
class TimeSlot:
    score: int
    workshop_indices: tuple[WorkshopIndex, ...]

@dataclass(frozen=True, order=True)
class TimeTable:
    score: int
    time_slots: tuple[TimeSlot, ...]
    @cached_property
    def workshop_indices(self) -> tuple[WorkshopIndex, ...]:
        return tuple(ws for ts in self.time_slots for ws in ts.workshop_indices)

@dataclass(frozen=True, kw_only=True, order=True)
class UnfinishedTimeTable:
    score_upper_bound: int
    next_time_slot_index: int
    time_table: TimeTable
    @property
    def score(self) -> int:
        return self.time_table.score
    @property
    def time_slots(self) -> tuple[TimeSlot, ...]:
        return self.time_table.time_slots
