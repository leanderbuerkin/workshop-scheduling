from collections import defaultdict
from collections.abc import Collection, Generator
from dataclasses import dataclass
from itertools import combinations
from random import randint, sample
from types import MappingProxyType

frozendict = MappingProxyType


@dataclass(frozen=True, kw_only=True, slots=True)
class Workshop:
    index: int
    name: str
    participants: frozenset[str]
    def __str__(self) -> str:
        return f"Workshop {self.name}: {", ".join(sorted(self.participants))}"


@dataclass(frozen=True, kw_only=True, slots=True)
class TimeSlot:
    workshops: frozenset[Workshop]
    @property
    def participants(self) -> frozendict[str, frozenset[Workshop]]:
        participants: dict[str, set[Workshop]] = defaultdict(set)
        for workshop in self.workshops:
            for participant in workshop.participants:
                participants[participant].add(workshop)
        return frozendict({participant: frozenset(options) for participant, options in participants.items()})
    @property
    def participants_with_exactly_one_option(self) -> frozendict[str, frozenset[Workshop]]:
        return frozendict({participant: options for participant, options in self.participants.items() if len(options) == 1})

    @property
    def score(self) -> int:
        """
        This score should always be smaller than the sum of the participants count of all workshops
        See [1]reference

        The current options are:
        - Number of participants that are interested in at least one workshop in this time slot
        - Number of participants that are interested in exactly  one workshop in this time slot

        The first option interprets the participants input more like
        "I find it important that this workshop takes place" and less like "I want to participate in this workshop".
        The result should be a tight time table
        where participants often have to choose between multiple workshops they like
        and every slot is full since there is no penalty for having multiple workshops at once.
        
        The second option returns only those workshops where a lot of people are interested
        and those workshop, where the participants submitted very little wishes (e.g. a special interest group).
        This option is considered a bit better,
        since only workshops take place, where it is "really worth it" - as far as the program can tell.
        """
        return len(self.participants_with_exactly_one_option)

    def __str__(self) -> str:
        output = f"Score {self.score}: "
        output += ", ".join(f"[{str(workshop)}]" for workshop in sorted(self.workshops, key=lambda w: len(w.participants), reverse=True))
        return output


@dataclass(frozen=True, kw_only=True, slots=True)
class TimeTable:
    time_slots: frozenset[TimeSlot]
    @property
    def score(self) -> int:
        return sum(time_slot.score for time_slot in self.time_slots)

    def can_be_extended(self, new_time_slot: TimeSlot) -> bool:
        for time_slot in self.time_slots:
            for workshop in time_slot.workshops:
                if workshop in new_time_slot.workshops:
                    return False
        return True
    
    def __str__(self) -> str:
        output = f"Allocation with score {self.score}:"
        for slot in sorted(self.time_slots, key=lambda slot: slot.score, reverse=True):
            output += f"\n  {str(slot)}"
        return output


def get_combinations_with_brute_force(
        workshops: Collection[Workshop],
        workshops_per_combination_max: int
    ) -> Generator[TimeSlot]:
    """
    Memory intensive since it generates all combinations and sorts them afterwards.

    This could be improved by using generators that yield combinations
    from the one with the highest sum of all participants to the one to the lowest.
    The sum of all participants should be the maximal score a combination could reach. [1]reference

    Using the combination that actually has the biggest score,
    one could generate only those combinations that could be bigger.
    """
    workshops_combinations = {
        TimeSlot(workshops=frozenset(workshops_combination))
        for workshops_per_combination in range(workshops_per_combination_max + 1)
        for workshops_combination in combinations(workshops, workshops_per_combination)
    }

    return (c for c in sorted(workshops_combinations, key=lambda c: c.score, reverse=True))

def get_combinations(
        workshops: Collection[Workshop],
        workshops_per_combination_max: int
    ) -> Generator[TimeSlot]:
    return get_combinations_with_brute_force(workshops, workshops_per_combination_max)


def get_solutions(
        workshops: Collection[Workshop],
        workshops_per_slot_max: int,
        time_slots_count: int
    ) -> Generator[TimeTable]:
    # todo: Problem: If a time table has one free slot and a high score
    # todo: it can happen, that the next time slot does not fit and finds a worse solution
    # todo: and afterwards a time slot with same or marginally lower score fits and fulfills a better solution
    # todo: for each solution we need to go through the time slots with the same score and add them and for each time slot we need to go through all solution
    # todo: Like 10 + 5 = 15 but also 9 + 6
    workshops = set(filter(lambda workshop: len(workshop.participants) > 0, workshops))

    potential_solutions: set[TimeTable] = {TimeTable(time_slots=frozenset())}
    for new_time_slot in get_combinations(workshops, workshops_per_slot_max):
        for potential_solution in sorted(potential_solutions, key=lambda s: s.score, reverse=True):
            if potential_solution.can_be_extended(new_time_slot):
                new_potential_solution = TimeTable(
                    time_slots=frozenset(potential_solution.time_slots.copy() | {new_time_slot})
                )

                if len(new_potential_solution.time_slots) < time_slots_count:
                    potential_solutions.add(new_potential_solution)
                elif len(new_potential_solution.time_slots) == time_slots_count:
                    yield new_potential_solution


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
