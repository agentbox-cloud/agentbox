from enum import Enum


class NodeType(str, Enum):
    BOARD = "board"
    NOMAD = "nomad"

    def __str__(self) -> str:
        return str(self.value)
