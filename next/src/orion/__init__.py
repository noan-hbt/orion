"""Orion: a team of persistent agents serving one person's goals."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("orion")
except PackageNotFoundError:
    __version__ = "0.0.1"

