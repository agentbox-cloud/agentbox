import platform

from importlib import metadata

try:
    version = metadata.version("agentbox-python-sdk")
except metadata.PackageNotFoundError:
    version = "dev"

default_headers = {
    "lang": "python",
    "lang_version": platform.python_version(),
    "machine": platform.machine(),
    "os": platform.platform(),
    "package_version": version,
    "processor": platform.processor(),
    "publisher": "agentbox",
    "release": platform.release(),
    "sdk_runtime": "python",
    "system": platform.system(),
}
