from collections.abc import Generator, Iterable
from heapq import heappop, heappush
from itertools import combinations

from data_structures import Preferences, ScoredTimeSlot, ScoredTimeTable, TimeTable, Workshop
def yield_time_tables(
        preferences: Preferences,
        workshops_per_time_slot: int,
        time_slots_per_time_table: int
    ) -> Generator[ScoredTimeTable]:

    def get_score(workshops: Iterable[Workshop]) -> int:
        total_score = 0
        participants_scores: tuple[int, ...]
        for participants_scores in zip(*(preferences[workshop] for workshop in workshops)):
            score = 0
            for participants_score in participants_scores:
                if score == 0:
                    score = participants_score
                elif participants_score != 0:
                    score = 0
                    break
            total_score += score
        return total_score

    time_slots: list[ScoredTimeSlot] = sorted(
        (get_score(combination), combination)
        for workshops_count in range(workshops_per_time_slot + 1)
        for combination in combinations(preferences.keys(), workshops_count)
    )

    unfinished_time_tables: set[TimeTable] = {tuple()}
    new_time_tables: set[TimeTable] = set()
    finished_time_tables: list[ScoredTimeTable] = list()
    best_unfinished_time_table_score = sum(score for score, _ in time_slots[:time_slots_per_time_table - 1])
    for new_time_slot in time_slots:
        future_time_table_scores_upper_bound = best_unfinished_time_table_score + new_time_slot[0]
        while len(finished_time_tables) > 0 and finished_time_tables[0][0] > future_time_table_scores_upper_bound:
            yield heappop(finished_time_tables)

        for unfinished_time_table in unfinished_time_tables:
            if any(
                workshop in new_time_slot[1]
                for time_slot in unfinished_time_table
                for workshop in time_slot[1]
                ):
                continue
            
            new_time_table = unfinished_time_table + (new_time_slot,)
            
            if len(new_time_table) == time_slots_per_time_table:
                score = sum(time_slot[0] for time_slot in new_time_table)
                # minus score cause its a min-heap
                heappush(finished_time_tables, (-score, new_time_table))
            elif len(new_time_table) < time_slots_per_time_table:
                new_time_tables.add(new_time_table)

        unfinished_time_tables.update(new_time_tables)
        new_time_tables.clear()

    for time_table in unfinished_time_tables:
        score = sum(time_slot[0] for time_slot in time_table)
        # minus score cause its a min-heap
        heappush(finished_time_tables, (-score, time_table))

    while len(finished_time_tables) > 0:
        yield heappop(finished_time_tables)
