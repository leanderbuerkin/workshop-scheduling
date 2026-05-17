from collections import defaultdict
from pathlib import Path

from data_structures import Preferences, frozendict

def read_workshops(path: Path) -> Preferences:
    participants_as_set: set[str] = set()
    workshops: dict[str, defaultdict[str, int]] = dict()
    workshop_name: str | None = None

    with open(path, "r") as file:
        for line in (raw_line.strip() for raw_line in file.readlines()):
            if line.startswith("## "):
                workshop_name = line[len("## "):].strip()
                workshops[workshop_name] = defaultdict(int)
                continue
            if line == "" or workshop_name is None:
                continue

            name, score = line.split(": ", 1)
            workshops[workshop_name][name] = int(score)
            participants_as_set.add(name)

    participants = sorted(participants_as_set)
    return frozendict({
        workshop: tuple(preferences[participant] for participant in participants)
        for workshop, preferences in workshops.items()
    })