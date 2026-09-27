import tests  # noqa: F401
"""
Verification that the offline network guard prevents any unmocked socket connections during tests.
"""

import socket
import unittest


class TestNetworkGuard(unittest.TestCase):
    """Ensure socket.connect raises RuntimeError during test execution."""

    def test_unmocked_socket_connect_raises(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            with self.assertRaises(RuntimeError) as ctx:
                s.connect(("1.1.1.1", 80))
            self.assertIn("NETWORK ACCESS FORBIDDEN", str(ctx.exception))
        finally:
            s.close()


if __name__ == "__main__":
    unittest.main()
