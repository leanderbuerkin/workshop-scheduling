from collections import defaultdict
from collections.abc import Iterable
from random import randint, sample

from data_structures import Workshop
from set_coverage_problem.solver import SetCoverageSolver


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

workshops = get_random_workshops(50, 50)
print("\n")
print("Workshops:\n")
print("\n".join(str(workshop) for workshop in workshops))
print("\n")

def convert_solution(solution: Union) -> set[TimeSlot]:



TRUE_INPUT = ("", "yes", "y", "true", "t", "1")
FALSE_INPUT = ("no", "n", "false", "f", "quit", "q", "exit", "e", "x", "0")

for solution in get_solutions(workshops, 3, 3):
    reply = input("Generate next solution? (answer enter/yes or no): ").lower().strip()
    if reply in TRUE_INPUT:
        print(solution)
    elif reply in FALSE_INPUT:
        break
    else:
        print(f"Please enter {"/".join(TRUE_INPUT)} or {"/".join(FALSE_INPUT)}")
