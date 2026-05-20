from bisect import insort
from collections.abc import Generator, Iterable
from functools import partial
from itertools import combinations
from typing import TypeAlias

from pandas import DataFrame

Workshop: TypeAlias = str
Score: TypeAlias = int
ScoreUpperBound: TypeAlias = int
Index = int

TimeSlot: TypeAlias = tuple[Score, tuple[Workshop, ...]]
UnfinishedTimeSlot: TypeAlias = tuple[ScoreUpperBound, Index, TimeSlot]
TimeTable: TypeAlias = tuple[Score, tuple[TimeSlot, ...]]
UnfinishedTimeTable: TypeAlias = tuple[ScoreUpperBound, Index, TimeTable]

# todo: Generate time_slots in a similar fashion:
# Remove all indizes that provide no benefit for themself or the given workshop
# Branch all of them and add self to 
# Iterate to the workshop that actually can be added
# todo: Use Numpy or rust

def yield_time_tables(
        preferences: DataFrame,
        time_slots_per_time_table: int
    ) -> Generator[tuple[int, tuple[tuple[int, tuple[str, ...]], ...]]]:
    time_slots = _get_time_slots(preferences)
    unfinished_time_tables: list[UnfinishedTimeTable] = list()
    finished_time_tables: list[TimeTable] = list()

    add_time_table = partial(
        _add_time_table,
        time_slots_per_time_table,
        time_slots,
        finished_time_tables,
        unfinished_time_tables
    )

    add_time_table(len(time_slots) - 1, (0, tuple()))

    while len(unfinished_time_tables) > 0:
        while len(finished_time_tables) > 0 and finished_time_tables[-1][0] >= unfinished_time_tables[-1][0]:
            yield finished_time_tables.pop()

        best_time_table = unfinished_time_tables.pop()

        new_time_slot_index = best_time_table[1]
        new_time_slot = time_slots[new_time_slot_index]

        new_time_slot_index = add_time_table(new_time_slot_index - 1, best_time_table[2])
        new_time_table = (best_time_table[2][0] + new_time_slot[0], best_time_table[2][1] + (new_time_slot,))
        add_time_table(new_time_slot_index, new_time_table)

    while len(finished_time_tables) > 0:
        yield finished_time_tables.pop()

def _get_time_slots(
        preferences: DataFrame,
        workshops_per_time_slot: int=3
        ) -> list[TimeSlot]:
    get_score = partial(_get_score, preferences)
    return sorted(
        (get_score(combination), combination)
        for workshops_count in range(1, workshops_per_time_slot + 1)
        for combination in combinations(preferences.columns, workshops_count)
    )

def get_time_slots(
        preferences: DataFrame
    ) -> list[TimeSlot]:
    get_score = partial(_get_score, preferences)

    time_slots: set[TimeSlot] = {(get_score((workshop,)), (workshop,)) for workshop in preferences.columns}
    old_length = 0
    while len(time_slots) > old_length:
        print(old_length)
        old_length = len(time_slots)
        time_slots.update(
            (score, time_slot1[1] + time_slot2[1])
            for time_slot1, time_slot2 in combinations(time_slots, 2)
            if (score := get_score(time_slot1[1] + time_slot2[1])) and score > time_slot1[0] and score > time_slot2[0]
        )

    return sorted(time_slots)

def _get_score(preferences: DataFrame, workshops: Iterable[str]) -> int:
    return sum(
        non_zero_scores[0]
        for participants_scores in zip(*(preferences[workshop] for workshop in workshops))
        if (non_zero_scores := tuple(s for s in participants_scores if s)) and len(non_zero_scores) == 1
    )

def _add_time_table(
        time_slots_per_time_table: int,
        time_slots: list[TimeSlot],
        finished_time_tables: list[TimeTable],
        unfinished_time_tables: list[UnfinishedTimeTable],
        new_time_slot_index: int,
        time_table: TimeTable
    ) -> int:
    while (
        new_time_slot_index > -1 and
        any(workshop in time_slots[new_time_slot_index][1] for time_slot in time_table[1] for workshop in time_slot[1])
        ):
        new_time_slot_index -= 1

    if new_time_slot_index == -1 or len(time_table[1]) >= time_slots_per_time_table:
        insort(finished_time_tables, time_table)
    else:
        stop = new_time_slot_index + 1
        start = stop - time_slots_per_time_table + len(time_table[1])
        insort(
            unfinished_time_tables,
            (
                time_table[0] + sum(time_slot[0] for time_slot in time_slots[start:stop]),
                new_time_slot_index,
                time_table
            )
        )

    return new_time_slot_index
