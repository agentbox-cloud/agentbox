from enum import Enum


class EnvType(str, Enum):
    ANDROID = "android"
    LINUX_ARM64 = "linux_arm64"
    LINUX_X86 = "linux_x86"

    def __str__(self) -> str:
        return str(self.value)
