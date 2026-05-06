from collections import Counter
from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class Scored:
    score: int


@dataclass(frozen=True, kw_only=True)
class SizedScored(Scored):
    def __len__(self) -> int:
        raise NotImplementedError("__len__() not implemented!")


@dataclass(frozen=True, kw_only=True)
class Workshop(Scored):
    index: int
    name: str
    participants: frozenset[str]

    def __str__(self) -> str:
        return f"{self.name} (score {self.score}): {", ".join(sorted(self.participants))}"


@dataclass(frozen=True, kw_only=True)
class TimeSlot(SizedScored):
    workshops: frozenset[Workshop]

    def __len__(self) -> int:
        return len(self.workshops)

    def __str__(self) -> str:
        output = f"Score {self.score}: "
        sorted_workshops = sorted(self.workshops, reverse=True, key=lambda w: w.score)
        output += ", ".join(f"[{workshop}]" for workshop in sorted_workshops)
        return output


def combine_to_time_slot(time_slot: TimeSlot, new_workshop: Workshop) -> TimeSlot | None:
    if new_workshop in time_slot.workshops:
        return None

    new_workshops = frozenset(time_slot.workshops | {new_workshop})
    participants = dict(Counter(
            participant
            for workshop in new_workshops
            for participant in workshop.participants
        ))
    new_score = sum(options_count for options_count in participants.values() if options_count == 1)
    return TimeSlot(score=new_score, workshops=new_workshops)


@dataclass(frozen=True, kw_only=True)
class TimeTable(SizedScored):
    time_slots: frozenset[TimeSlot]

    def __len__(self) -> int:
        return len(self.time_slots)

    def __str__(self) -> str:
        output = f"\nTimeTable (score {self.score})"
        for time_slot in self.time_slots:
            output += f"\n  {time_slot}"
        return output + "\n"


def combine_to_time_table(time_table: TimeTable, new_time_slot: TimeSlot) -> TimeTable | None:
    if new_time_slot in time_table.time_slots:
        return None
    for time_slot in time_table.time_slots:
        for workshop in time_slot.workshops:
            if workshop in new_time_slot.workshops:
                return None

    new_time_slots = frozenset(time_table.time_slots | {new_time_slot})
    new_score = sum(time_slot.score for time_slot in new_time_slots)
    return TimeTable(score=new_score, time_slots=new_time_slots)
