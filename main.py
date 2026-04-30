from random import randint, sample

from data_structures import TimeSlot, TimeTable, Workshop
from optimal_union_finder import FindOptimalUnionIterator

# todo: compress into single file, that reads a txt and returns the result as txt

def get_random_workshops(workshops_count: int, participants_count: int) -> frozenset[Workshop]:
    participants = [str(index) for index in range(participants_count)]
    return frozenset({
        Workshop(
            index=workshop_index,
            name=str(workshop_index),
            participants=frozenset(sample(participants, k=randint(0, len(participants)//2)))
        )
        for workshop_index in range(workshops_count)
    })


workshops = get_random_workshops(10, 10)
print("\n")
print("Workshops:\n")
print("\n".join(str(workshop) for workshop in workshops))
print("\n")

time_slot_finder = FindOptimalUnionIterator[Workshop, TimeSlot](
    unions_max_length=3,
    root_union=TimeSlot(workshops=frozenset()),
    elements_descending_by_score=workshops
)
time_table_finder = FindOptimalUnionIterator[TimeSlot, TimeTable](
    unions_max_length=3,
    root_union=TimeTable(time_slots=frozenset()),
    elements_descending_by_score=time_slot_finder
)

TRUE_INPUT = ("", "yes", "y", "true", "t", "1")
# FALSE_INPUT = ("no", "n", "false", "f", "quit", "q", "exit", "e", "x", "0")

for solution in time_table_finder:
    print(solution)
    reply = input("Generate next solution? (answer enter/yes or no): ").lower().strip()
    if reply not in TRUE_INPUT:
        break
