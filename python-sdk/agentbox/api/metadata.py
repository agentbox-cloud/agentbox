import platform

from importlib import metadata

try:
    package_version = metadata.version("agentbox-python-sdk")
except metadata.PackageNotFoundError:
    package_version = "dev"

default_headers = {
    "lang": "python",
    "lang_version": platform.python_version(),
    "machine": platform.machine(),
    "os": platform.platform(),
    "package_version": package_version,
    "processor": platform.processor(),
    "publisher": "agentbox",
    "release": platform.release(),
    "sdk_runtime": "python",
    "system": platform.system(),
}
