from collections.abc import Generator, Iterable

from data_structures import TimeSlot, TimeTable, Workshop

class OptimalTimeSlotFinder:
    _workshops_per_time_slot_max: int
    _unfinished_time_slots: set[frozenset[Workshop]]
    _finished_time_slots: set[TimeSlot]

    def __init__(self):
        pass

    def yield_best_time_slot(
            self,
            workshops: Iterable[Workshop],
            workshops_per_time_slot_max: int
        ) -> Generator[TimeSlot]:
        if workshops_per_time_slot_max < 1:
            yield TimeSlot(workshops=frozenset())
            return
        self._unfinished_time_slots = {frozenset()}
        self._finished_time_slots = set()
        self._workshops_per_time_slot_max = workshops_per_time_slot_max
    
        for workshop in sorted(workshops, key=lambda w: w.score, reverse=True):
            self._add_workshop_to_time_slots(workshop)
            yieldable_score_lower_bound = self._get_future_scores_upper_bound(workshop.score)
            yield from self._yield_yieldable_time_slots(yieldable_score_lower_bound)
    
        self._finished_time_slots.update(
            TimeSlot(workshops=unfinished_time_slot)
            for unfinished_time_slot in self._unfinished_time_slots
        )
        yield from self._yield_yieldable_time_slots(0)
    
    def _add_workshop_to_time_slots(self, workshop: Workshop):
        for unfinished_time_slot in self._unfinished_time_slots.copy():
            new_time_slot = frozenset(unfinished_time_slot | {workshop})
            if len(new_time_slot) == self._workshops_per_time_slot_max:
                self._finished_time_slots.add(TimeSlot(workshops=new_time_slot))
            else:
                self._unfinished_time_slots.add(new_time_slot)
    
    def _get_future_scores_upper_bound(
            self,
            score_of_missing_workshops_upper_bound: int
        ) -> int:
        upper_bound_max = 0
        for unfinished_time_slot in self._unfinished_time_slots:
            missing_workshops_count = self._workshops_per_time_slot_max - len(unfinished_time_slot)
            upper_bound = (
                sum(workshop.score for workshop in unfinished_time_slot) +
                missing_workshops_count * score_of_missing_workshops_upper_bound
            )
            upper_bound_max = max(upper_bound_max, upper_bound)
        return upper_bound_max
    
    def _yield_yieldable_time_slots(
            self,
            yieldable_score_lower_bound: int
        ) -> Generator[TimeSlot]:
        sorted_finished_time_slots = sorted(
            self._finished_time_slots,
            key=lambda time_slot: time_slot.score,
            reverse=True
        )
        for time_slot in sorted_finished_time_slots:
            if time_slot.score > yieldable_score_lower_bound:
                yield time_slot
                self._finished_time_slots.remove(time_slot)
            else:
                break

class OptimalTimeTableFinder:
    _time_slots_per_time_table: int
    _unfinished_time_tables: set[frozenset[TimeSlot]]
    _finished_time_tables: set[TimeTable]

    def __init__(self):
        pass

    def yield_best_time_table(
            self,
            workshops: Iterable[Workshop],
            workshops_per_time_slot_max: int,
            time_slots_per_time_table: int
        ) -> Generator[TimeTable]:
        if time_slots_per_time_table < 1:
            yield TimeTable(time_slots=frozenset())
            return
        self._unfinished_time_tables = {frozenset()}
        self._finished_time_tables = set()
        self._time_slots_per_time_table = time_slots_per_time_table

        time_slot_generator = OptimalTimeSlotFinder().yield_best_time_slot(
            workshops,
            workshops_per_time_slot_max
        )

        for time_slot in time_slot_generator:
            self._add_time_slot_to_time_tables(time_slot)
            yieldable_score_lower_bound = self._get_future_scores_upper_bound(time_slot.score)
            yield from self._yield_yieldable_time_tables(yieldable_score_lower_bound)
        
        self._finished_time_tables.update(
            TimeTable(time_slots=unfinished_time_table)
            for unfinished_time_table in self._unfinished_time_tables
        )
        yield from self._yield_yieldable_time_tables(0)
    
    def _add_time_slot_to_time_tables(self, time_slot: TimeSlot):
        for unfinished_time_table in self._unfinished_time_tables.copy():
            if self.have_overlapping_workshop(unfinished_time_table, time_slot):
                continue
            new_time_table = frozenset(unfinished_time_table | {time_slot})
            if len(new_time_table) == self._time_slots_per_time_table:
                self._finished_time_tables.add(TimeTable(time_slots=new_time_table))
            else:
                self._unfinished_time_tables.add(new_time_table)

    def _get_future_scores_upper_bound(
            self,
            score_of_missing_workshops_upper_bound: int
        ):
        upper_bound_max = 0
        for unfinished_time_table in self._unfinished_time_tables:
            missing_time_slots_count = self._time_slots_per_time_table - len(unfinished_time_table)
            upper_bound = (
                sum(time_slot.score for time_slot in unfinished_time_table) +
                missing_time_slots_count * score_of_missing_workshops_upper_bound
            )
            upper_bound_max = max(upper_bound_max, upper_bound)
        return upper_bound_max

    def _yield_yieldable_time_tables(
            self,
            yieldable_score_lower_bound: int
        ):
        sorted_finished_time_tables = sorted(
            self._finished_time_tables,
            key=lambda time_table: time_table.score,
            reverse=True
        )
        for time_table in sorted_finished_time_tables:
            if time_table.score > yieldable_score_lower_bound:
                yield time_table
                self._finished_time_tables.remove(time_table)
            else:
                break

    @staticmethod
    def have_overlapping_workshop(time_slots: Iterable[TimeSlot], new_time_slot: TimeSlot) -> bool:
        return any(
            workshop in new_time_slot.workshops
            for time_slot in time_slots
            for workshop in time_slot.workshops
        )
