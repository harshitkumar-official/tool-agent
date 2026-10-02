import os
import tempfile
import unittest

from agent import Agent, calculate, convert


class ToolTests(unittest.TestCase):
    def test_calculate(self):
        self.assertEqual(calculate("12*(3+4)"), "84")
        self.assertEqual(calculate("10/4"), "2.5")
        self.assertEqual(calculate("2**3"), "8")

    def test_calculate_rejects_code(self):
        with self.assertRaises(ValueError):
            calculate("__import__('os').system('echo hi')")

    def test_divide_by_zero(self):
        with self.assertRaises(ZeroDivisionError):
            calculate("1/0")

    def test_convert(self):
        self.assertEqual(convert(100, "c", "f"), "212.00 f")
        self.assertEqual(convert(10, "km", "miles"), "6.21 miles")
        with self.assertRaises(ValueError):
            convert(1, "kg", "km")


class AgentTests(unittest.TestCase):
    def setUp(self):
        self.agent = Agent(os.path.join(tempfile.mkdtemp(), "n.json"))

    def test_routes_to_calculator(self):
        self.assertEqual(self.agent.handle("what is 6*7"), "42")
        self.assertEqual(self.agent.trace[-1], "calculate")

    def test_routes_to_converter(self):
        self.assertEqual(self.agent.handle("convert 5 km to miles"), "3.11 miles")
        self.assertEqual(self.agent.trace[-1], "convert")

    def test_notes_add_and_search(self):
        self.agent.handle("note: buy a Java book")
        self.assertIn("Java", self.agent.handle("find notes java"))
        self.assertEqual(self.agent.handle("find notes python"), "No matching notes.")

    def test_notes_persist_to_disk(self):
        path = os.path.join(tempfile.mkdtemp(), "n.json")
        Agent(path).handle("note: remember viva")
        self.assertIn("viva", Agent(path).handle("search notes viva"))

    def test_unknown_request(self):
        self.assertIn("I can calculate", self.agent.handle("tell me a joke"))
        self.assertEqual(self.agent.trace[-1], "none")

    def test_tool_error_is_reported_not_raised(self):
        self.assertIn("failed", self.agent.handle("calc 1/0"))


if __name__ == "__main__":
    unittest.main()
