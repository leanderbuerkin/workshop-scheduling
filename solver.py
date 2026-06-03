from heapq import heapify, heappop, heappush
from itertools import combinations
from time import time

from numpy import ndarray
from pandas import read_csv
from pathlib import Path

type Length = int
type Score = int
type ScoreUpperBound = int

type WorkshopName = str
type WorkshopIndex = int

type TimeSlot = frozenset[WorkshopIndex]
type TimeTable = tuple[TimeSlot, ...]

CSV_INPUT_FILE_PATH = Path("example.csv")

TIME_TABLES_TARGET_LENGTH = 20
MAX_FINAL_TIME_TABLES = 100
OUTPUT_FILE_PATH = Path("best_time_table_per_length.md")

SECONDS_BETWEEN_TERMINAL_PRINTS = 1
SECONDS_BETWEEN_SAVES_TO_FILE = 120
MAXIMUM_TIME_TABLES_FOR_MEMORY_SAFETY = 1_000_000
IGNORE_FIRST_CSV_COLUMN = True  # E.g. if the names are in the first column


def _read_csv_file(csv_path: Path) -> tuple[ndarray, tuple[WorkshopName, ...]]:
    if IGNORE_FIRST_CSV_COLUMN:
        raw = read_csv(csv_path, index_col=0).fillna(0)
    else:
        raw = read_csv(csv_path).fillna(0)
    normalized = raw.div(raw.sum(axis=1), axis=0)
    sorted_column_names = normalized.sum(axis=0).sort_values().index
    sorted = normalized[sorted_column_names]
    return sorted.to_numpy(), tuple(sorted_column_names)


def _get_time_slots(preferences: ndarray) -> tuple[tuple[Score, TimeSlot], ...]:
    workshops_total_count = preferences.shape[1]
    print(f"Generating feasible time slots from {workshops_total_count:,} workshops...")

    time_slots: list[tuple[WorkshopIndex, ...]] = [tuple()]
    scores: dict[tuple[WorkshopIndex, ...], int] = dict()

    for new_workshop_index in range(workshops_total_count):
        for time_slot_index in range(len(time_slots)):
            new_time_slot = time_slots[time_slot_index] + (new_workshop_index,)
            if new_time_slot not in scores.keys():
                scores[new_time_slot] = _get_time_slot_score(preferences, new_time_slot)

            subsets = (
                subset
                for time_slot_length in range(1, len(new_time_slot))
                for subset in combinations(new_time_slot, time_slot_length)
            )
            for subset in subsets:
                if subset not in scores.keys():
                    scores[subset] = _get_time_slot_score(preferences, subset)
                if scores[subset] >= scores[new_time_slot]:
                    break
            else:
                time_slots.append(new_time_slot)

    time_slots.remove(tuple())
    print(f"Generated {len(time_slots):,} time slots.")
    return tuple(sorted((scores[time_slot], frozenset(time_slot)) for time_slot in time_slots))


def _get_compatible_time_slots(
        time_slots: tuple[tuple[Score, TimeSlot], ...]
    ) -> dict[TimeSlot, frozenset[tuple[Score, TimeSlot]]]:
    """The compatible time slots have always a lower score then the time slot itself."""
    compatible_time_slots: dict[TimeSlot, frozenset[tuple[Score, TimeSlot]]] = {
        frozenset(): frozenset(time_slots)
    }
    checked_time_slots: list[tuple[Score, TimeSlot]] = list()
    for time_slot_score, time_slot in sorted(time_slots):
        compatible_time_slots[time_slot] = frozenset(
            (other_time_slot_score, other_time_slot)
            for other_time_slot_score, other_time_slot in checked_time_slots
            if len(other_time_slot & time_slot) == 0
        )
        checked_time_slots.append((time_slot_score, time_slot))
    return compatible_time_slots


def _get_time_slot_score(preferences: ndarray, workshop_indices: tuple[WorkshopIndex, ...]) -> int:
    covered_preferences = preferences[:, workshop_indices]
    value_counts = (covered_preferences != 0).sum(axis=1)
    return covered_preferences[value_counts == 1].sum(axis=1).sum()


def get_time_tables(csv_path: Path):
    preferences, workshop_names = _read_csv_file(csv_path)
    time_slots = _get_time_slots(preferences)
    print("Generating Time Tables...")
    compatible_time_slots = _get_compatible_time_slots(time_slots)

    time_tables: list[tuple[ScoreUpperBound, Score, TimeTable, list[tuple[Score, TimeSlot]]]] = [
        (0, 0, tuple(), sorted(time_slots))
    ]
    heapify(time_tables)
    finished_time_tables: list[tuple[Score, TimeTable]] = list()
    lowest_final_score = -1
    finished_time_tables_count = 0
    checked_time_tables_count = 0
    time_at_last_print = 0
    time_at_last_save = 0

    while len(time_tables) > 0:
        if len(time_tables) > MAXIMUM_TIME_TABLES_FOR_MEMORY_SAFETY:
            time_tables.sort()
            time_tables = time_tables[:MAXIMUM_TIME_TABLES_FOR_MEMORY_SAFETY//10]
            heapify(time_tables)

        score_upper_bound, score, time_table, expansions = heappop(time_tables)
        score_upper_bound = -score_upper_bound
        checked_time_tables_count += 1
        if len(time_table) + len(expansions) < TIME_TABLES_TARGET_LENGTH:
            continue
        if score_upper_bound <= lowest_final_score:
            continue
        new_time_slot_score, new_time_slot = expansions.pop()
        missing_time_slots_count = TIME_TABLES_TARGET_LENGTH - len(time_table)
        score_upper_bound = score + sum(s for s, _ in expansions[-missing_time_slots_count:])
        # Negative score_upper_bound to use min-heap
        heappush(time_tables, (-score_upper_bound, score, time_table, expansions))

        new_time_table = time_table + (new_time_slot,)
        new_score = score + new_time_slot_score

        if len(new_time_table) == TIME_TABLES_TARGET_LENGTH:
            finished_time_tables_count += 1
            finished_time_tables.append((new_score, new_time_table))
            if len(finished_time_tables) > MAX_FINAL_TIME_TABLES:
                finished_time_tables.sort()
                finished_time_tables.pop(0)
                lowest_final_score = finished_time_tables[0][0]
            continue

        new_expansions = sorted(
            compatible_time_slots[new_time_slot].intersection(expansions)
        )
        new_missing_time_slots_count = TIME_TABLES_TARGET_LENGTH - len(new_time_table)
        new_score_upper_bound = new_score + sum(s for s, _ in new_expansions[-new_missing_time_slots_count:])
        # Negative score_upper_bound to use min-heap
        heappush(time_tables, (-new_score_upper_bound, new_score, new_time_table, new_expansions))

        if time() - time_at_last_print > SECONDS_BETWEEN_TERMINAL_PRINTS:
            time_at_last_print = time()
            biggest_length = max(len(tt) for _, _, tt, _ in time_tables)
            print(
                f"Checked {checked_time_tables_count:,} time tables, " +
                f"{finished_time_tables_count:,} time tables with target length were found, " +
                f"{len(time_tables):,} can be expanded, " +
                f"the longest contains {biggest_length} time slots."
            )

        if time() - time_at_last_save > SECONDS_BETWEEN_SAVES_TO_FILE:
            time_at_last_save = time()
            if len(finished_time_tables) != 0:
                _save_time_tables_to_file(workshop_names, finished_time_tables)


def _save_time_tables_to_file(
        workshop_names: tuple[WorkshopName, ...],
        time_tables: list[tuple[int, TimeTable]]
    ):
    with open(OUTPUT_FILE_PATH, "w") as output_file:
        output_file.write("# Best Time Tables\n")
        for score, time_table in sorted(time_tables, reverse=True):
            output_file.write(f"\n\nScore {score:.2f} Length {len(time_table)}:")
            for time_slot in time_table:
                workshops = ", ".join(str(workshop_names[workshop_index]) for workshop_index in time_slot)
                output_file.write(f"\n  {workshops}")
        output_file.write("\n")
    print(
        f"Saved {len(time_tables):,} time tables to file " \
        f"{OUTPUT_FILE_PATH}."
    )

get_time_tables(CSV_INPUT_FILE_PATH)
