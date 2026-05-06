from bisect import insort
from pathlib import Path

from data_structures import Workshop


def read_workshops(path: Path) -> list[Workshop]:
    workshops: list[Workshop] = []
    workshop_name: str | None = None

    with open(path, "r") as file:
        for line in (raw_line.strip() for raw_line in file.readlines()):
            if line.startswith("## "):
                workshop_name = line[len("## "):].strip()
            elif line != "" and workshop_name:
                participants = frozenset(participant.strip() for participant in line.split(","))
                insort(
                    workshops,
                    Workshop(
                        score=len(participants),
                        index=len(workshops),
                        name=workshop_name,
                        participants=participants
                    ),
                    key=lambda workshop: workshop.score
                )
                workshop_name = None

    return workshops