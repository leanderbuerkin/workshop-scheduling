from pathlib import Path

from data_structures import TimeSlot, TimeTable, combine_to_time_slot, combine_to_time_table
from reader import read_workshops
from solver import yield_best_unions

# todo: Allow the participants to set preferences

sorted_workshops = read_workshops(Path("example.md"))
sorted_time_slots = yield_best_unions(
    elements_high_to_low=(workshop for workshop in sorted_workshops),
    elements_per_union=3,
    root_union=TimeSlot(score=0, workshops=frozenset()),
    combine=combine_to_time_slot
)

sorted_time_tables = yield_best_unions(
    elements_high_to_low=sorted_time_slots,
    elements_per_union=20,
    root_union=TimeTable(score=0, time_slots=frozenset()),
    combine=combine_to_time_table
)

TRUE_INPUT = ("", "yes", "y", "true", "enter", "t", "1")
# FALSE_INPUT = ("no", "n", "false", "f", "quit", "q", "exit", "e", "x", "0")

for solution in sorted_time_tables:
    print(solution)
    reply = input("Generate next solution? (answer enter/yes or no): ").lower().strip()
    if reply not in TRUE_INPUT:
        break
