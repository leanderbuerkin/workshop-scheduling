from random import randint, sample

from data_structures import Workshop
from solver import OptimalTimeTableFinder

# todo: merge solver into one generic one that handles time tables and time slots?
# todo: reduce memory usage and/or processing time (cache things, handle indices instead of classes)
# todo: print status: difference between score_upper_bound and score
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

solver = OptimalTimeTableFinder()


TRUE_INPUT = ("", "yes", "y", "true", "t", "1")
# FALSE_INPUT = ("no", "n", "false", "f", "quit", "q", "exit", "e", "x", "0")

for solution in solver.yield_best_time_table(workshops, 3, 3):
    print(solution)
    reply = input("Generate next solution? (answer enter/yes or no): ").lower().strip()
    if reply not in TRUE_INPUT:
        break
