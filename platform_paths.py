"""Translate native paths for Panda3D on Windows, macOS and Linux."""
from panda3d.core import Filename


def panda_path(path):
    return Filename.fromOsSpecific(str(path)).getFullpath()
