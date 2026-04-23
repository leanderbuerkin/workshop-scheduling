from collections.abc import Generator, Iterable

from data_structures import TimeSlot, TimeTable, Workshop


class OptimalTimeSlotsFinder:
    unbeatable_time_slots: list[TimeSlot]
    _unfinished_time_slots: set[TimeSlot]
    _finished_time_slots: set[TimeSlot]

    def __init__(self, workshops: Iterable[Workshop], workshops_per_slot: int):
        self.unbeatable_time_slots = list()
        self._unfinished_time_slots = set()
        self._finished_time_slots = set()
        self._unfinished_time_slots.add(TimeSlot(
            workshops=frozenset(),
            addable_workshops=frozenset(workshops),
            workshops_count_target=workshops_per_slot
        ))

    def yield_best_time_slots(self) -> Generator[TimeSlot]:
        self._finished_time_slots |= set(self.unbeatable_time_slots)
        self.unbeatable_time_slots = list()
        while len(self._unfinished_time_slots) > 0:
            yield from self._yield_new_unbeatable_time_slots()
            most_promising_time_slot = self._pop_most_promising_time_slot()
            if most_promising_time_slot.expandable:
                self._unfinished_time_slots.update(most_promising_time_slot.expansions)
            else:
                self._finished_time_slots.add(most_promising_time_slot)

    def _yield_new_unbeatable_time_slots(self) -> Generator[TimeSlot]:
        if len(self._unfinished_time_slots) == 0:
            undiscovered_score_upper_bound = 0
        else:
            undiscovered_score_upper_bound = max(
                time_slot.score_upper_bound
                for time_slot in self._unfinished_time_slots
            )
        for time_slot in sorted(self._finished_time_slots, key=lambda time_slot: time_slot.score, reverse=True):
            if time_slot.score < undiscovered_score_upper_bound:
                break
            self._finished_time_slots.remove(time_slot)
            self.unbeatable_time_slots.append(time_slot)
            yield time_slot

    def _pop_most_promising_time_slot(self) -> TimeSlot:
        if not self._unfinished_time_slots:
            raise ValueError("No unfinished time slot to pop.")
        most_promising_time_slot = max(
            self._unfinished_time_slots,
            key=lambda time_slot: time_slot.score_upper_bound
        )
        self._unfinished_time_slots.remove(most_promising_time_slot)
        return most_promising_time_slot

    def _add_time_slots(self, time_slots: Iterable[TimeSlot]):
        for time_slot in time_slots:
            self._add_time_slot(time_slot)
    
    def _add_time_slot(self, time_slot: TimeSlot):
        if time_slot.expandable:
            self._unfinished_time_slots.add(time_slot)
        else:
            self._finished_time_slots.add(time_slot)


# TimeTableFinder must generate time_slots till it can not be better.

class OptimalTimeTableFinder:
    unbeatable_time_tables: list[TimeTable]
    _unfinished_time_tables: set[TimeTable]
    _finished_time_tables: set[TimeTable]
    _time_slots_generator: Generator[TimeSlot]  # Assumed to be infinite

    def __init__(
            self,
            workshops: Iterable[Workshop],
            time_slots_per_time_table: int,
            workshops_per_slot: int
        ):
        self.unbeatable_time_tables = list()
        self._unfinished_time_tables = set()
        self._finished_time_tables = set()
        self._unfinished_time_tables.add(TimeTable(
            time_slots=frozenset(),
            addable_time_slots=frozenset(),
            time_slots_count_target=time_slots_per_time_table
        ))
        self._time_slots_generator = OptimalTimeSlotsFinder(
                workshops=workshops,
                workshops_per_slot=workshops_per_slot
            ).yield_best_time_slots()
    
    def yield_best_time_table(self) -> Generator[TimeTable]:
        self._finished_time_tables |= set(self.unbeatable_time_tables)
        self.unbeatable_time_tables = list()
        while len(self._unfinished_time_tables) > 0:
            self._add_time_slots_if_needed()
            yield from self._yield_new_unbeatable_time_slots()
            most_promising_time_table = self._pop_most_promising_time_table()
            if most_promising_time_table.expandable:
                self._unfinished_time_tables.update(most_promising_time_table.expansions)
            else:
                self._finished_time_tables.add(most_promising_time_table)

    def _add_time_slots_if_needed(self):
        while any(time_table.needs_time_slots for time_table in self._unfinished_time_tables):
            new_time_slot = next(self._time_slots_generator)

            new_time_tables: set[TimeTable] = set()
            for time_table in self._unfinished_time_tables:
                if any(time_table.contains(workshop) for workshop in new_time_slot.workshops):
                    new_time_tables.add(time_table)
                else:
                    new_time_tables.add(TimeTable(
                        time_slots=time_table.time_slots,
                        addable_time_slots=frozenset(time_table.addable_time_slots | {new_time_slot}),
                        time_slots_count_target=time_table.time_slots_count_target
                    ))
            self._unfinished_time_tables = new_time_tables

    def _yield_new_unbeatable_time_slots(self) -> Generator[TimeTable]:
        if len(self._unfinished_time_tables) == 0:
            undiscovered_score_upper_bound = 0
        else:
            undiscovered_score_upper_bound = max(
                time_table.score_upper_bound
                for time_table in self._unfinished_time_tables
            )
        for time_table in sorted(self._finished_time_tables, key=lambda time_table: time_table.score, reverse=True):
            if time_table.score < undiscovered_score_upper_bound:
                break
            self._finished_time_tables.remove(time_table)
            self.unbeatable_time_tables.append(time_table)
            yield time_table
    
    def _pop_most_promising_time_table(self) -> TimeTable:
        if not self._unfinished_time_tables:
            raise ValueError("No unfinished time table to pop.")
        most_promising_time_table = max(
            self._unfinished_time_tables,
            key=lambda time_table: time_table.score_upper_bound
        )
        self._unfinished_time_tables.remove(most_promising_time_table)
        return most_promising_time_table