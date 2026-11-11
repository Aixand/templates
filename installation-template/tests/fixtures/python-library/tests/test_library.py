import unittest

from fixture_library import greet


class LibraryTest(unittest.TestCase):
    def test_public_api_and_packaged_resource(self):
        self.assertEqual(greet("世界"), "Hello, 世界!")
