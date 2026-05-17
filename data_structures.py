
from types import MappingProxyType
from typing import TypeAlias

frozendict = MappingProxyType

Participant: TypeAlias = int
Workshop: TypeAlias = str
Score: TypeAlias = int

Preferences: TypeAlias = frozendict[Workshop, tuple[Score, ...]]

TimeSlot: TypeAlias = tuple[Workshop, ...]
ScoredTimeSlot: TypeAlias = tuple[Score, TimeSlot]
TimeTable: TypeAlias = tuple[ScoredTimeSlot, ...]
ScoredTimeTable: TypeAlias = tuple[Score, TimeTable]
