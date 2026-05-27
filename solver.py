from bisect import insort
from collections.abc import Generator, Sequence
from functools import partial
from numpy import ndarray

from data_structures import TimeSlot, TimeTable, UnfinishedTimeTable, WorkshopIndex

def yield_time_tables(
        time_slots_in_descending_order: list[TimeSlot],
        time_slots_per_time_table: int
    ) -> Generator[TimeTable]:
    unfinished_time_tables: list[UnfinishedTimeTable] = list()
    finished_time_tables: list[TimeTable] = list()

    add_time_table = partial(
        _add_time_table,
        time_slots_per_time_table,
        time_slots_in_descending_order,
        finished_time_tables,
        unfinished_time_tables
    )

    add_time_table(0, TimeTable(score=0, time_slots=tuple()))

    while len(unfinished_time_tables) > 0:
        print(len(unfinished_time_tables))
        if len(finished_time_tables) > 0:
            print(f"Score: {finished_time_tables[-1].score}")
            print(f"Upper Bound: {unfinished_time_tables[-1].score_upper_bound}")
        while len(finished_time_tables) > 0 and finished_time_tables[-1].score >= unfinished_time_tables[-1].score_upper_bound:
            yield finished_time_tables.pop()
        
        best_time_table = unfinished_time_tables.pop()

        new_time_slot_index = best_time_table.next_time_slot_index
        new_time_slot = time_slots_in_descending_order[new_time_slot_index]

        new_time_slot_index = add_time_table(new_time_slot_index + 1, best_time_table.time_table)
        new_time_table = TimeTable(
            score=best_time_table.score + new_time_slot.score,
            time_slots=best_time_table.time_slots + (new_time_slot,)
        )
        add_time_table(new_time_slot_index, new_time_table)
    
    while len(finished_time_tables) > 0:
        yield finished_time_tables.pop()


def _add_time_table(
        time_slots_per_time_table: int,
        time_slots_in_descending_order: list[TimeSlot],
        finished_time_tables: list[TimeTable],
        unfinished_time_tables: list[UnfinishedTimeTable],
        new_time_slot_index: int,
        time_table: TimeTable
    ) -> int:
    while (
        new_time_slot_index < len(time_slots_in_descending_order) and
        any(
            workshop in time_slots_in_descending_order[new_time_slot_index].workshop_indices
            for workshop in time_table.workshop_indices
        )
        ):
        new_time_slot_index += 1
    
    if (
        new_time_slot_index == len(time_slots_in_descending_order) or
        len(time_table.time_slots) >= time_slots_per_time_table
        ):
        insort(finished_time_tables, time_table)
    else:
        start = new_time_slot_index
        stop = start + time_slots_per_time_table - len(time_table.time_slots)
        insort(
            unfinished_time_tables,
            UnfinishedTimeTable(
                score_upper_bound=time_table.score + sum(
                    time_slot.score
                    for time_slot in time_slots_in_descending_order[start:stop]
                ),
                next_time_slot_index=new_time_slot_index,
                time_table=time_table
            )
        )
    
    return new_time_slot_index
    

def get_time_slots(preferences: ndarray) -> list[TimeSlot]:
    get_score = partial(_get_score, preferences)

    unfinished_time_slots: set[TimeSlot] = {
        TimeSlot(get_score((workshop_index,)), (workshop_index,))
        for workshop_index in range(preferences.shape[1])
    }
    time_slots: set[TimeSlot] = set()

    while len(unfinished_time_slots) > 0:
        time_slot = unfinished_time_slots.pop()
        time_slots.add(time_slot)

        for workshop_index in range(min(time_slot.workshop_indices)):
            expanded_workshop_indices = time_slot.workshop_indices + (workshop_index,)
            score = get_score(expanded_workshop_indices)
            if score > time_slot.score:
                unfinished_time_slots.add(TimeSlot(score, expanded_workshop_indices))

    return sorted(time_slots, reverse=True)

def _get_score(preferences: ndarray, workshop_indices: Sequence[WorkshopIndex]) -> int:
    covered_preferences = preferences[:, workshop_indices]
    value_counts = (covered_preferences != 0).sum(axis=1)
    return covered_preferences[value_counts == 1].sum(axis=1).sum()
