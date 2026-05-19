from bisect import insort
from collections import defaultdict
from collections.abc import Generator
from heapq import merge
from itertools import combinations

from data_structures import Preferences, ScoredTimeSlot, ScoredTimeTable, Workshop

# todo: ram usage also depends on parameters
# RAM usage for 3 workshops per time slot and 3 time sots per time table
# 200: 56 MB
# 400: 483 MB
# 600: 1.9 GB
# 800: 4.9 GB
MAXIMUM_ELEMENTS_PER_COMBINATION = 50

def yield_time_tables(
        preferences: Preferences,
        workshops_per_time_slot: int,
        time_slots_per_time_table: int
    ) -> Generator[ScoredTimeTable]:

    def get_score(workshops: tuple[Workshop, ...]) -> int:
        return sum(
            non_zero_scores[0]
            for participants_scores in zip(*(preferences[workshop] for workshop in workshops))
            if (non_zero_scores := tuple(s for s in participants_scores if s)) and len(non_zero_scores) == 1
        )

    time_slots: list[ScoredTimeSlot] = sorted(
        (
            (get_score(combination), combination)
            for workshops_count in range(1, workshops_per_time_slot + 1)
            for combination in combinations(preferences.keys(), workshops_count)
        ),
        reverse=True
    )

    unfinished_time_tables: defaultdict[int, list[ScoredTimeTable]] = defaultdict(list)
    unfinished_time_tables[time_slots_per_time_table].append((0, tuple()))
    finished_time_tables: list[ScoredTimeTable] = list()

    for index, new_time_slot in enumerate(time_slots):
        upper_bound_future_time_tables = max(
            time_tables[-1][0] + sum(ts[0] for ts in time_slots[index: index + missing_time_slots_count])
            for missing_time_slots_count, time_tables in unfinished_time_tables.items()
        )
        print(f"Upper bound: {upper_bound_future_time_tables}")
        if len(finished_time_tables) > 0:
            print(f"Next best score: {finished_time_tables[-1][0]}")

        if len(finished_time_tables) > 0 and finished_time_tables[-1][0] >= upper_bound_future_time_tables:
            yield finished_time_tables.pop()

        for time_table in [time_table for time_tables in unfinished_time_tables.values() for time_table in time_tables]:
                if any(workshop in new_time_slot[1] for time_slot in time_table[1] for workshop in time_slot[1]):
                    continue
                new_time_table = (time_table[0] + new_time_slot[0], time_table[1] + (new_time_slot,))
                if len(new_time_table[1]) == time_slots_per_time_table:
                    insort(finished_time_tables, new_time_table)
                else:
                    insort(unfinished_time_tables[time_slots_per_time_table - len(new_time_table[1])], new_time_table)
                    if len(unfinished_time_tables[time_slots_per_time_table - len(new_time_table[1])]) > 1000:
                        unfinished_time_tables[time_slots_per_time_table - len(new_time_table[1])].pop(0)

    finished_time_tables_as_generator = iter(finished_time_tables)
    for time_tables in unfinished_time_tables.values():
        finished_time_tables_as_generator = merge(finished_time_tables_as_generator, time_tables)
    yield from finished_time_tables_as_generator
