from pathlib import Path
from pandas import read_csv

from solver import get_time_slots, yield_time_tables

ACCURACY_OF_NORMALIZATION = 1000000

# todo: If you normalizes it runs very long

raw_preferences_as_dataframe = read_csv(Path("example.csv"), index_col=0).fillna(0).astype(int)
workshop_names = tuple(raw_preferences_as_dataframe.columns)
raw_preferences = raw_preferences_as_dataframe.to_numpy(dtype=int)

row_sums = raw_preferences.sum(axis=1, keepdims=True)
preferences = (ACCURACY_OF_NORMALIZATION * raw_preferences) // row_sums

print("Generating time slots...")
time_slots = get_time_slots(preferences)
print(f"Generated {len(time_slots)} time slots.")
print("Generating first time table...")
sorted_time_tables = yield_time_tables(time_slots, 10)

TRUE_INPUT = ("", "yes", "y", "true", "enter", "t", "1")
# FALSE_INPUT = ("no", "n", "false", "f", "quit", "q", "exit", "e", "x", "0")



for solution in sorted_time_tables:
    print(f"Score {solution.score}")
    for time_slot in solution.time_slots:
        print(f"  {time_slot.score}: {", ".join(workshop_names[workshop_index] for workshop_index in time_slot.workshop_indices)}")
    reply = input("Generate next solution? (answer enter/yes or no): ").lower().strip()
    if reply not in TRUE_INPUT:
        break
