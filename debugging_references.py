from collections.abc import Iterable
from functools import partial
from itertools import combinations

from pandas import DataFrame

from data_structures import TimeSlot

def get_time_slots_by_brute_force(
        preferences: DataFrame,
        workshop_names: tuple[str, ...],
        workshops_per_time_slot_max: int=3
    ) -> list[TimeSlot]:
    get_score = partial(_get_score, preferences)
    return sorted(
        (
            TimeSlot(get_score(combination), tuple(workshop_names.index(workshop) for workshop in combination))
            for workshops_count in range(1, workshops_per_time_slot_max + 1)
            for combination in combinations(reversed(workshop_names), workshops_count)
        ),
        reverse=True
    )

def _get_score(
        preferences: DataFrame,
        workshops: Iterable[str]
    ) -> int:
    return sum(
        non_zero_scores[0]
        for participants_scores in zip(*(preferences[workshop] for workshop in workshops))
        if (non_zero_scores := tuple(s for s in participants_scores if s)) and len(non_zero_scores) == 1
    )
