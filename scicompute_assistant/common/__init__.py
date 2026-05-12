"""Shared library used by both the server and the offline desktop entry points.

The goal of this package is to host >=90% of the application logic so that the
FastAPI server (deployed on a teaching cluster) and the Tauri desktop build
(distributed to students) can be assembled from the same source of truth.
"""

__all__ = [
    "ai",
    "compute",
    "knowledge",
    "protocols",
    "security",
    "utils",
]
