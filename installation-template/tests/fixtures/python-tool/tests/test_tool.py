import unittest

from fixture_tool import describe


class ToolTest(unittest.TestCase):
    def test_dependency_and_resource(self):
        self.assertEqual(
            describe("bücher.example"), "Installed resource: xn--bcher-kva.example"
        )
