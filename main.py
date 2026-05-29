from bisect import insort
from itertools import combinations
from pathlib import Path

from numpy import ndarray
from pandas import read_csv

CSV_INPUT_FILE_PATH = Path("example.csv")
TIME_TABLE_MAX_LEN = 20
ACCURACY_OF_NORMALIZATION = 1_000_000


type WorkshopIndex = int
type TimeSlot = tuple[WorkshopIndex, ...]
type TimeSlotIndex = int
type TimeTable = tuple[tuple[TimeSlot, ...], frozenset[WorkshopIndex]]

def _read_csv_file(csv_path: Path) -> tuple[ndarray, tuple[str, ...]]:
    raw_preferences_as_dataframe = read_csv(csv_path, index_col=0).fillna(0).astype(int)

    workshop_names = tuple(raw_preferences_as_dataframe.columns)

    raw_preferences = raw_preferences_as_dataframe.to_numpy(dtype=int)
    row_sums = raw_preferences.sum(axis=1, keepdims=True)
    preferences = (ACCURACY_OF_NORMALIZATION * raw_preferences) // row_sums

    return preferences, workshop_names

def _get_time_slots(preferences: ndarray) -> dict[TimeSlot, int]:
    time_slots: dict[TimeSlot, int] = {tuple(): 0}

    workshops_count = preferences.shape[1]
    for workshop_index in range(workshops_count):
        print(f"{workshop_index + 1}/{workshops_count}")
        for time_slot in sorted(time_slots.keys(), key=lambda ts: len(ts)):
            new_time_slot = time_slot + (workshop_index,)
            score = _get_score(preferences, new_time_slot)
            if any(
                time_slots[subset] >= score
                for workshop_count in range(1, len(new_time_slot))
                for subset in combinations(new_time_slot, workshop_count)
                if subset in time_slots.keys()
                ):
                continue
            time_slots[new_time_slot] = score
    del time_slots[tuple()]
    return time_slots

def _get_score(preferences: ndarray, workshop_indices: tuple[WorkshopIndex, ...]) -> int:
    covered_preferences = preferences[:, workshop_indices]
    value_counts = (covered_preferences != 0).sum(axis=1)
    return covered_preferences[value_counts == 1].sum(axis=1).sum()

def _get_time_tables_sorted_by_length(
        time_slots: dict[TimeSlot, int]
    ) -> list[TimeTable]:
    time_tables: list[TimeTable] = [(tuple(), frozenset())]
    scores: dict[tuple[WorkshopIndex, ...], int] = {tuple(): 0}

    # workshop_occurences = sorted(
    #     Counter(workshop for time_slot in time_slots.keys() for workshop in time_slot).items(),
    #     key=lambda x: x[1],
    #     reverse=True
    # )
    # cohorts: list[list[TimeSlot]] = [list(time_slots.keys())]
    # for most_present_workshop in (ws for ws, _ in workshop_occurences):
    #     last_cohort = cohorts.pop()
    #     time_slots_with_workshop = [ts for ts in last_cohort if most_present_workshop in ts]
    #     time_slots_without_workshop = [ts for ts in last_cohort if most_present_workshop not in ts]
    #     if len(time_slots_with_workshop) > 0:
    #         cohorts.append(time_slots_with_workshop)
    #     if len(time_slots_without_workshop) > 0:
    #         cohorts.append(time_slots_without_workshop)

    counter = 0
    # for cohort in cohorts:
    for new_time_slot, _ in sorted(time_slots.items(), key=lambda ts__score: ts__score[1], reverse=True)[:500]:
        counter += 1
        print(f"{counter}/{len(time_slots)}")
        print(len(time_tables))
        if len(time_tables) > 200_000:
            time_tables.sort(key=lambda time_table: scores[tuple(time_table[1])])
            return time_tables
        new_workshops = frozenset(new_time_slot)
        for time_table_index in range(len(time_tables)):
            time_table = time_tables[time_table_index]
            covered_workshops = time_table[1] | new_workshops
            if len(time_table[1]) + len(new_workshops) != len(covered_workshops):
                continue
            new_time_slots = time_table[0] + (new_time_slot,)
            new_score = sum(time_slots[ts] for ts in new_time_slots) // (len(time_table) + 1)
            if any(
                scores[subset] >= new_score
                for workshop_count in range(1, len(covered_workshops))
                for subset in combinations(covered_workshops, workshop_count)
                if subset in scores.keys()
                ):
                continue
            scores[tuple(covered_workshops)] = new_score
            insort(
                time_tables,
                (new_time_slots, covered_workshops),
                key=lambda time_table: len(time_table[1])
            )
    time_tables.sort(key=lambda time_table: scores[tuple(time_table[1])])
    return time_tables

# def _print_time_table(
#         time_tables_sorted_by_length: list[TimeTable],
#         workshop_names: tuple[str, ...]
#         ):
#     for length, time_tables_of_equal_length in time_tables_sorted_by_length.items():
#         time_tables_of_equal_length.sort()
#         makedirs("output", exist_ok=True) # todo: Make path and proper
#         with open(f"output/time_tables_with_length_{length}", "w") as file:
#             while len(time_tables_of_equal_length) > 0:
#                 time_table = time_tables_of_equal_length.pop()
#                 file.write(f"Score: {time_table[0]}\n")
#                 for time_slot in time_table[1]:
#                     file.write(f"  {time_slot[0]}: ")
#                     file.write(", ".join(workshop_names[workshop_index] for workshop_index in time_slot[1]))
#                     file.write("\n")


print("Reading CSV...")
preferences, workshop_names = _read_csv_file(CSV_INPUT_FILE_PATH)
print(f"Generating time slots from {preferences.shape[1]} workshops...")
time_slots = _get_time_slots(preferences)
print(f"Generating time tables from {len(time_slots)} time slots...")
time_tables = _get_time_tables_sorted_by_length(time_slots)
print(f"Printing {len(time_tables)} time tables...")
#for time_table, _ in reversed(time_tables):
#    print(f"Score: {sum(time_slots[time_slot] for time_slot in time_table)}")
#    for time_slot in time_table:
#        print(
#            f"  {time_slots[time_slot]}:" +
#            ", ".join(workshop_names[workshop_index] for workshop_index in time_slot)
#        )
# _print_time_table(time_tables, workshop_names)
