from pathlib import Path
from reader import read_workshops
from solver import yield_time_tables

preferences = read_workshops(Path("long_example.md"))

sorted_time_tables = yield_time_tables(preferences, 3, 20)

TRUE_INPUT = ("", "yes", "y", "true", "enter", "t", "1")
# FALSE_INPUT = ("no", "n", "false", "f", "quit", "q", "exit", "e", "x", "0")

for solution in sorted_time_tables:
    print(f"Score {solution[0]}")
    for time_slot in solution[1]:
        print(f"  {time_slot}")
    reply = input("Generate next solution? (answer enter/yes or no): ").lower().strip()
    if reply not in TRUE_INPUT:
        break
