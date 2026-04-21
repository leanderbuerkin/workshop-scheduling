
from collections import defaultdict
from collections.abc import Generator, Iterable

from config import WORKSHOPS_PER_SLOT
from data_structures import TimeSlot, TimeTable, Workshop
from set_coverage_problem.solver import SetCoverageSolver, Union

# generate time tables and yield them if no better time table could be generated.

def yield_time_tables(workshops: Iterable[Workshop]) -> Generator[TimeTable]:

    unfinished_time_tables: set[frozenset[TimeSlot]] = {frozenset()}
    finished_time_tables: set[frozenset[TimeSlot]] = set()
    unbeatable_time_tables: set[frozenset[TimeSlot]] = set()
    for time_slot in _yield_time_slots(workshops):
        undiscovered_time_tables_score_upper_bound = max(
            
        )

def _get_score_upper_bound(unfinished_time_table: frozenset[TimeSlot]) -> int:
    for TimeSlot in unfinished_time_table:


def _yield_time_slots(workshops: Iterable[Workshop]) -> Generator[TimeSlot]:
    mapping = _get_sets(workshops)
    solver = SetCoverageSolver(
        mapping.keys(),
        operands_count_upper_bound=WORKSHOPS_PER_SLOT
    )
    for union in solver.yield_best_unions():
        for time_slot in convert_to_time_slots(union, mapping):
            yield time_slot

def _get_sets(
        workshops: Iterable[Workshop]
    ) -> dict[frozenset[str], frozenset[Workshop]]:
    sets: defaultdict[frozenset[str], set[Workshop]] = defaultdict(set)
    for workshop in workshops:
        sets[workshop.participants].add(workshop)
    return {key: frozenset(value) for key, value in sets.items()}

def convert_to_time_slots(
        union: Union,
        mapping: dict[frozenset[str], frozenset[Workshop]]
    ) -> Generator[TimeSlot]:
    time_slots: set[frozenset[Workshop]] = set()
    for _set in union.sets:
        for time_slot in set(time_slots):
            for workshop in mapping[_set]:
                time_slots.add(frozenset(time_slot | {workshop}))
    return (TimeSlot(workshops=time_slot) for time_slot in time_slots)
