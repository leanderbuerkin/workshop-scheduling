
from bisect import insort
from collections import defaultdict
from collections.abc import Generator
from pathlib import Path

from numpy import ndarray
from pandas import read_csv

CSV_INPUT_FILE_PATH = Path("example.csv")
MAXIMUM_LENGTH_OF_TIME_TABLE = 10
MAXIMUM_BRANCHES_COUNT = 100_000 # decrease to reduce time and memory consumption
ACCURACY_OF_NORMALIZATION = 1_000_000


type WorkshopIndex = int
type TimeSlot = tuple[int, frozenset[WorkshopIndex]]
type TimeTable = tuple[int, tuple[TimeSlot, ...]]

def _read_csv_file(csv_path: Path) -> tuple[ndarray, tuple[str, ...]]:
    raw_preferences_as_dataframe = read_csv(csv_path, index_col=0).fillna(0).astype(int)
    workshop_names = tuple(raw_preferences_as_dataframe.columns)
    raw_preferences = raw_preferences_as_dataframe.to_numpy(dtype=int)

    row_sums = raw_preferences.sum(axis=1, keepdims=True)
    preferences = (ACCURACY_OF_NORMALIZATION * raw_preferences) // row_sums

    return preferences, workshop_names

def _get_time_slots(preferences: ndarray) -> list[TimeSlot]:
    time_slots: list[TimeSlot] = [(0, frozenset())]

    workshops_count = preferences.shape[1]
    for workshop_index in range(workshops_count):
        print(f"{workshop_index}/{workshops_count}")
        for time_slot in time_slots.copy():
            expanded_workshop_indices = time_slot[1] | {workshop_index}
            score = _get_score(preferences, expanded_workshop_indices)
            if score > time_slot[0]:
                insort(time_slots, (score, expanded_workshop_indices))

    return time_slots

def _get_score(preferences: ndarray, workshop_indices: frozenset[WorkshopIndex]) -> int:
    covered_preferences = preferences[:, tuple(workshop_indices)]
    value_counts = (covered_preferences != 0).sum(axis=1)
    return covered_preferences[value_counts == 1].sum(axis=1).sum()

def _get_time_tables(time_slots: list[TimeSlot]) -> defaultdict[int, list[TimeTable]]:
    original_length_of_time_slots = len(time_slots)
    time_tables: list[TimeTable] = [(0, tuple())]
    time_tables_sorted_by_length: defaultdict[int, list[TimeTable]] = defaultdict(list)

    while len(time_slots) > 0:
        time_slot = time_slots.pop()

        print(f"Remaining steps:    {original_length_of_time_slots - len(time_slots)}/{original_length_of_time_slots}")
        print(f"Number of branches: {len(time_tables)}/{MAXIMUM_BRANCHES_COUNT}")

        if len(time_tables) > MAXIMUM_BRANCHES_COUNT:
            del time_tables[:len(time_tables)- MAXIMUM_BRANCHES_COUNT]
        if len(time_tables_sorted_by_length[MAXIMUM_LENGTH_OF_TIME_TABLE]) > MAXIMUM_BRANCHES_COUNT:
            del time_tables_sorted_by_length[MAXIMUM_LENGTH_OF_TIME_TABLE][
                :len(time_tables_sorted_by_length[MAXIMUM_LENGTH_OF_TIME_TABLE])- MAXIMUM_BRANCHES_COUNT
            ]

        for time_table in time_tables.copy():
            if len(time_table) == MAXIMUM_LENGTH_OF_TIME_TABLE:
                continue
            if time_slot[1].isdisjoint(_get_workshops(time_table)):
                if len(time_table[1]) + 1 == MAXIMUM_LENGTH_OF_TIME_TABLE:
                    insort(
                        time_tables_sorted_by_length[MAXIMUM_LENGTH_OF_TIME_TABLE],
                        (time_table[0] + time_slot[0], time_table[1] + (time_slot,))
                    )
                else:
                    insort(time_tables, (time_table[0] + time_slot[0], time_table[1] + (time_slot,)))

    while len(time_tables) > 0:
        time_table = time_tables.pop()
        time_tables_sorted_by_length[len(time_table[1])].append(time_table)

    return time_tables_sorted_by_length

def _get_workshops(time_table: TimeTable) -> Generator[WorkshopIndex]:
    return (workshop_index for time_slot in time_table[1] for workshop_index in time_slot[1])

def _print_time_table(
        time_tables_sorted_by_length: defaultdict[int, list[TimeTable]],
        workshop_names: tuple[str, ...]
        ):
    for length, time_tables_of_equal_length in time_tables_sorted_by_length.items():
        with open(f"time_tables_with_length_{length}", "w") as file:
            for time_table in time_tables_of_equal_length:
                file.write(f"Score: {time_table[0]}\n")
                for time_slot in time_table[1]:
                    file.write(f"  {time_slot[0]}: ")
                    file.write(", ".join(workshop_names[workshop_index] for workshop_index in time_slot[1]))
                    file.write("\n")


print("Reading CSV...")
preferences, workshop_names = _read_csv_file(CSV_INPUT_FILE_PATH)
print("Generating time slots...")
time_slots = _get_time_slots(preferences)
print("Generating time tables...")
time_tables = _get_time_tables(time_slots)
print("Printing time tables...")
_print_time_table(time_tables, workshop_names)
