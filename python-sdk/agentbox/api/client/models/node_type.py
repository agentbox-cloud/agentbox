from enum import Enum


class NodeType(str, Enum):
    BOARD = "board"
    NOMAD_ARM64 = "nomad_arm64"
    NOMAD_X86 = "nomad_x86"

    def __str__(self) -> str:
        return str(self.value)
