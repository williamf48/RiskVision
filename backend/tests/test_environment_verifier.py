import sys
import unittest
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))


from verify_environment import verify_environment


class EnvironmentVerifierTests(unittest.TestCase):

    def test_reproducible_fixture_is_complete(self):
        verify_environment()


if __name__ == "__main__":
    unittest.main(verbosity=2)
