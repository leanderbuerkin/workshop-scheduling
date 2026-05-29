from bisect import insort
from collections import defaultdict
from collections.abc import Generator
from itertools import combinations
from time import time

from numpy import ndarray
from pandas import Index, read_csv
from pathlib import Path

# todo: store the workshops covered by expandable and expanded time slots:
# todo: if any time table with same length and higher score covered those workshops or more
# todo: Discard the current one (in which order do I need to built these?)

type Workshop = str
type WorkshopIndex = int
type TimeSlot = tuple[WorkshopIndex, ...]
type TimeTable = tuple[TimeSlot, ...]

CSV_INPUT_FILE_PATH = Path("example.csv")
ACCURACY_OF_NORMALIZATION = 1_000_000
SECONDS_BETWEEN_SAVES = 600

def _read_csv_file(csv_path: Path) -> tuple[ndarray, Index]:
    raw = read_csv(csv_path, index_col=0).fillna(0)
    normalized = raw.div(raw.sum(axis=1), axis=0)
    sorted_column_names = normalized.sum(axis=0).sort_values().index
    sorted = normalized[sorted_column_names]
    return sorted.to_numpy(), sorted_column_names

def _get_time_slots(preferences: ndarray) -> tuple[tuple[TimeSlot, ...], dict[TimeSlot, int]]:
    time_slots: list[TimeSlot] = [tuple()]
    scores: dict[TimeSlot, int] = dict()
    workshops_total_count = preferences.shape[1]

    for workshop_index in range(workshops_total_count):
        print(f"{workshop_index + 1}/{workshops_total_count}")

        for time_slot_index in range(len(time_slots)):
            new_time_slot = time_slots[time_slot_index] + (workshop_index,)
            new_score = _get_score(preferences, new_time_slot)
            scores[new_time_slot] = new_score

            subsets = (
                subset
                for workshop_count in range(len(new_time_slot))
                for subset in combinations(new_time_slot, workshop_count)
            )
            for subset in subsets:
                if subset not in scores.keys():
                    scores[subset] = _get_score(preferences, subset)
                if scores[subset] >= new_score:
                    break
            else:
                time_slots.append(new_time_slot)

    time_slots.remove(tuple())
    return tuple(time_slots), scores

def _get_score(preferences: ndarray, workshop_indices: tuple[WorkshopIndex, ...]) -> int:
    covered_preferences = preferences[:, workshop_indices]
    value_counts = (covered_preferences != 0).sum(axis=1)
    return covered_preferences[value_counts == 1].sum(axis=1).sum()

def yield_time_tables(
        time_slots: tuple[TimeSlot, ...],
        time_slot_scores: dict[TimeSlot, int]
    ) -> Generator[list[tuple[int, TimeTable]]]:
    time_slots_copy = list(time_slots)
    compatible_time_slots: dict[TimeSlot, frozenset[TimeSlot]] = {tuple(): frozenset(time_slots)}
    while len(time_slots_copy) > 0:
        time_slot = time_slots_copy.pop()
        compatible_time_slots[time_slot] = frozenset(
            other_time_slot
            for other_time_slot in time_slots_copy
            if len(set(time_slot) & set(other_time_slot)) == 0
        )

    time_tables_by_length: dict[int, list[tuple[int, TimeTable]]] = defaultdict(list)
    time_tables_by_length[0] = [(0, tuple())]
    expansions: dict[int, dict[TimeTable, frozenset[TimeSlot]]] = {0: {tuple(): frozenset(time_slots)}}
    time_tables_by_expansions: dict[int, dict[frozenset[TimeSlot], TimeTable]] = {0: {frozenset(time_slots): tuple()}}
    expanded_time_tables: dict[int, list[tuple[int, TimeTable]]] = defaultdict(list)
    time_at_last_safe = time()

    minimal_length = 0
    while len(time_tables_by_length.keys()) > 0:
        for length in list(time_tables_by_length.keys()):
            if len(time_tables_by_length[length]) == 0:
                del time_tables_by_length[length]
                if length == minimal_length:
                    minimal_length += 1 
                continue

            score, time_table = time_tables_by_length[length].pop()

            for new_time_slot in expansions[length][time_table]:
                new_time_table = time_table + (new_time_slot,)
                new_score = score + time_slot_scores[new_time_slot]
                new_expansion = (expansions[length][time_table] - {new_time_slot}).intersection(compatible_time_slots[new_time_slot])
                if new_expansion in time_tables_by_expansions[length].keys():
                    if time_tables_by_expansions[length][time]
                        insort(time_tables_by_length[length + 1], (new_score, new_time_table))

            if minimal_length == length:
                print(", ".join(f"{length}: {len(tts)}" for length, tts in time_tables_by_length.items()))
            insort(expanded_time_tables[length], (score, time_table))
            if len(expanded_time_tables[length]) > 10:
                expanded_time_tables[length].pop(0)

        if time() - time_at_last_safe > SECONDS_BETWEEN_SAVES:
            time_at_last_safe = time()
            yield [tt for best_time_tables in expanded_time_tables.values() for tt in best_time_tables[-10:]]

preferences, workshop_names = _read_csv_file(csv_path=CSV_INPUT_FILE_PATH)
time_slots, time_slot_scores = _get_time_slots(preferences)

for time_tables in yield_time_tables(time_slots, time_slot_scores):
    print("Updated Time Table!")
    with open("output.md", "w") as output_file:
        output_file.write("# Best Time Tables")
        for time_table in reversed(time_tables):
            output_file.write(f"\n\nScore {int(time_table[0]*100)} Length {len(time_table[1])}:")
            for time_slot in time_table[1]:
                workshops = ", ".join(str(workshop_names[i]) for i in time_slot)
                output_file.write(f"\n  {workshops}")
        output_file.write("\n")
