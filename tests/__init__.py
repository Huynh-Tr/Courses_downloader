"""
Test bootstrap and offline network guard for Coursera_downloader characterization tests.
"""

import argparse
import socket
import sys
from unittest.mock import MagicMock

# 1. Shims for missing third-party packages in clean/offline environments.
# This ensures characterization tests run on standard Python 3.10+ without modifying system packages.

if "configargparse" not in sys.modules:
    sys.modules["configargparse"] = argparse
    argparse.ArgParser = argparse.ArgumentParser


class _DummyVersion:
    """Lightweight comparator matching packaging.version.Version behavior for test assertions."""

    def __init__(self, v):
        parts = []
        for piece in str(v).split("."):
            num = ""
            for ch in piece:
                if ch.isdigit():
                    num += ch
                else:
                    break
            parts.append(int(num) if num else 0)
        self._parts = tuple(parts[:3])

    def __ge__(self, other):
        other_parts = other._parts if isinstance(other, _DummyVersion) else _DummyVersion(other)._parts
        return self._parts >= other_parts

    def __gt__(self, other):
        other_parts = other._parts if isinstance(other, _DummyVersion) else _DummyVersion(other)._parts
        return self._parts > other_parts

    def __le__(self, other):
        other_parts = other._parts if isinstance(other, _DummyVersion) else _DummyVersion(other)._parts
        return self._parts <= other_parts

    def __lt__(self, other):
        other_parts = other._parts if isinstance(other, _DummyVersion) else _DummyVersion(other)._parts
        return self._parts < other_parts

    def __eq__(self, other):
        other_parts = other._parts if isinstance(other, _DummyVersion) else _DummyVersion(other)._parts
        return self._parts == other_parts


if "packaging" not in sys.modules:
    _pkg = MagicMock()
    _pkg.version.Version = _DummyVersion
    _pkg.version.parse = _DummyVersion
    sys.modules["packaging"] = _pkg
    sys.modules["packaging.version"] = _pkg.version

if "bs4" not in sys.modules:
    _bs4 = MagicMock()
    _bs4.__version__ = "4.13.4"
    sys.modules["bs4"] = _bs4

if "rookiepy" not in sys.modules:
    sys.modules["rookiepy"] = MagicMock()


# 2. Strict offline network guard to guarantee no live external network access during tests.
_real_connect = socket.socket.connect


def _guarded_connect(self, *args, **kwargs):
    raise RuntimeError(
        "NETWORK ACCESS FORBIDDEN: Unit tests must run completely offline without external network sockets."
    )


socket.socket.connect = _guarded_connect
