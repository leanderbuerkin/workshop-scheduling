from collections import defaultdict
from heapq import heappop, heappush, heapify, heappushpop
from itertools import combinations
from time import time

from numpy import ndarray
from pandas import read_csv
from pathlib import Path

type Length = int
type Score = int
type WorkshopName = str
type WorkshopIndex = int
type TimeSlot = frozenset[WorkshopIndex]
type TimeTable = tuple[TimeSlot, ...]


CSV_INPUT_FILE_PATH = Path("example.csv")
BEST_TIME_TABLE_PER_LENGTH_OUTPUT_MARKDOWN_FILE_PATH = Path("best_time_table_per_length.md")
BEST_TIME_TABLES_PER_LENGTH_OUTPUT_MARKDOWN_FILE_PATH = Path("best_time_tables_per_length.md")
NUMBER_OF_TIME_TABLES_PER_LENGTH_TO_SAVE_TO_FILE = 100
SECONDS_BETWEEN_TERMINAL_PRINTS = 0.5
SECONDS_BETWEEN_SAVES_TO_FILE = 10
MAXIMUM_TIME_TABLES_FOR_MEMORY_SAFETY = 100_000  # Is normaly never reached
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
    new_time_slots: list[tuple[WorkshopIndex, ...]] = list()
    scores: dict[tuple[WorkshopIndex, ...], int] = dict()

    for new_workshop_index in range(workshops_total_count):
        print(f"Workshop {new_workshop_index + 1:,}/{workshops_total_count:,} processed.")

        for time_slot in time_slots:
            new_time_slot = time_slot + (new_workshop_index,)
            new_score = _get_time_slot_score(preferences, new_time_slot)
            scores[new_time_slot] = new_score

            subsets = (
                subset
                for time_slot_length in range(len(new_time_slot))
                for subset in combinations(new_time_slot, time_slot_length)
            )
            for subset in subsets:
                if subset not in scores.keys():
                    scores[subset] = _get_time_slot_score(preferences, subset)
                if scores[subset] >= new_score:
                    break
            else:
                new_time_slots.append(new_time_slot)
        
        time_slots.extend(new_time_slots)
        new_time_slots.clear()

    print(f"Generated {len(time_slots):,} time slots.")
    return tuple(sorted((scores[time_slot], frozenset(time_slot)) for time_slot in time_slots))


def _get_time_slot_score(preferences: ndarray, workshop_indices: tuple[WorkshopIndex, ...]) -> int:
    covered_preferences = preferences[:, workshop_indices]
    value_counts = (covered_preferences != 0).sum(axis=1)
    return covered_preferences[value_counts == 1].sum(axis=1).sum()


def _get_compatible_time_slots(
        time_slots: tuple[tuple[Score, TimeSlot], ...]
    ) -> dict[TimeSlot, frozenset[tuple[Score, TimeSlot]]]:
    compatible_time_slots: dict[TimeSlot, frozenset[tuple[Score, TimeSlot]]] = dict()
    checked_time_slots: list[tuple[Score, TimeSlot]] = list()
    # not using reverse=True because time_slots are maybe already sorted
    for score, time_slot in reversed(sorted(time_slots)):
        compatible_time_slots[time_slot] = frozenset(
            (other_score, other_time_slot)
            for other_score, other_time_slot in checked_time_slots
            if len(other_time_slot & time_slot) == 0
        )
        checked_time_slots.append((score, time_slot))
    return compatible_time_slots


def _save_time_tables_to_file(
        workshop_names: tuple[WorkshopName, ...],
        time_tables: dict[Length, list[tuple[int, TimeTable]]]
    ):
    time_tables_count = sum(len(tts) for tts in time_tables.values())
    with open(BEST_TIME_TABLES_PER_LENGTH_OUTPUT_MARKDOWN_FILE_PATH, "w") as output_file:
        output_file.write("# Best Time Tables\n")
        output_file.write(
            "\nCheckout the " +
            str(BEST_TIME_TABLES_PER_LENGTH_OUTPUT_MARKDOWN_FILE_PATH) +
            " which contains only the best time table per length."
        )
    with open(BEST_TIME_TABLES_PER_LENGTH_OUTPUT_MARKDOWN_FILE_PATH, "a") as output_file:
        for length in sorted(time_tables.keys(), reverse=True):
            output_file.write(f"\n\n## Length {length}")
            for score, time_table in sorted(time_tables[length], reverse=True):
                output_file.write(f"\n\nScore {score:.2f} Length {len(time_table)}:")
                for time_slot in time_table:
                    workshops = ", ".join(str(workshop_names[workshop_index]) for workshop_index in time_slot)
                    output_file.write(f"\n  {workshops}")
        output_file.write("\n")
    print(
        f"Saved {time_tables_count:,} time tables to file " \
        f"{BEST_TIME_TABLES_PER_LENGTH_OUTPUT_MARKDOWN_FILE_PATH}."
    )

    with open(BEST_TIME_TABLE_PER_LENGTH_OUTPUT_MARKDOWN_FILE_PATH, "w") as output_file:
        output_file.write("# Best Time Table Per Length\n")
        output_file.write(
            "\nCheckout the " +
            str(BEST_TIME_TABLES_PER_LENGTH_OUTPUT_MARKDOWN_FILE_PATH) +
            " which contains all " +
            str(NUMBER_OF_TIME_TABLES_PER_LENGTH_TO_SAVE_TO_FILE) +
            " best time tables per length."
        )
    with open(BEST_TIME_TABLE_PER_LENGTH_OUTPUT_MARKDOWN_FILE_PATH, "a") as output_file:
        for length in sorted(time_tables.keys(), reverse=True):
            score, time_table = max(time_tables[length])
            output_file.write(f"\n\nScore {score:.2f} Length {len(time_table)}:")
            for time_slot in time_table:
                workshops = ", ".join(str(workshop_names[workshop_index]) for workshop_index in time_slot)
                output_file.write(f"\n  {workshops}")
        output_file.write("\n")
    print(
        f"Saved {time_tables_count:,} time tables to file " \
        f"{BEST_TIME_TABLE_PER_LENGTH_OUTPUT_MARKDOWN_FILE_PATH}."
    )



def generate_time_tables(csv_path: Path):
    preferences, workshop_names = _read_csv_file(csv_path)
    time_slots = _get_time_slots(preferences)
    print("Generating Time Tables...")
    compatible_time_slots = _get_compatible_time_slots(time_slots)

    time_tables: list[tuple[Score, tuple[TimeSlot, ...], frozenset[tuple[Score, TimeSlot]]]] = [
        (-time_slot_score, (time_slot,), compatible_time_slots[time_slot])  # negative score for min sort
        for time_slot_score, time_slot in time_slots
    ]
    heapify(time_tables)
    finished_time_tables: dict[Length, list[tuple[int, TimeTable]]] = defaultdict(list)
    finished_time_tables_count = 0
    time_at_last_print = time()
    time_at_last_save = time()


    while len(time_tables) > 0:
        score, time_table, expansions = heappop(time_tables)

        if len(finished_time_tables[len(time_table)]) > NUMBER_OF_TIME_TABLES_PER_LENGTH_TO_SAVE_TO_FILE:
            heappushpop(finished_time_tables[len(time_table)], (-score, time_table))
        else:
            heappush(finished_time_tables[len(time_table)], (-score, time_table))
        finished_time_tables_count += 1

        for new_time_slot_score, new_time_slot in expansions:
            new_time_table = time_table + (new_time_slot,)
            new_score = score - new_time_slot_score  # negative score for min sort
            new_expansions = expansions & compatible_time_slots[new_time_slot]
            heappush(time_tables, (new_score, new_time_table, new_expansions))

        if len(time_tables) > MAXIMUM_TIME_TABLES_FOR_MEMORY_SAFETY:
            time_tables = sorted(time_tables)[:MAXIMUM_TIME_TABLES_FOR_MEMORY_SAFETY//10]
            heapify(time_tables)

        if time() - time_at_last_print > SECONDS_BETWEEN_TERMINAL_PRINTS:
            time_at_last_print = time()
            print(f"{finished_time_tables_count:,} time tables checked, {len(time_tables):,} can be expanded.")

        if time() - time_at_last_save > SECONDS_BETWEEN_SAVES_TO_FILE:
            time_at_last_save = time()
            _save_time_tables_to_file(workshop_names, finished_time_tables)

generate_time_tables(CSV_INPUT_FILE_PATH)
