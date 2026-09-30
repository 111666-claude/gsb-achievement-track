import unittest

from achievements.core import Achievements


class ReportTest(unittest.TestCase):
    def test_progress_increases(self):
        book = Achievements()
        book.report("e1", "slayer", 3, 10)
        self.assertEqual(book.progress_of("slayer"), 3)

    def test_not_done_before_target(self):
        book = Achievements()
        book.report("e1", "slayer", 3, 10)
        self.assertFalse(book.is_done("slayer"))


class QueryTest(unittest.TestCase):
    def test_unknown_achievement_is_zero(self):
        self.assertEqual(Achievements().progress_of("missing"), 0)

    def test_scanned_starts_at_zero(self):
        self.assertEqual(Achievements().scanned_count(), 0)


if __name__ == "__main__":
    unittest.main()
