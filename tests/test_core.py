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


class IdempotencyTest(unittest.TestCase):
    def test_duplicate_event_id_counts_once(self):
        book = Achievements()
        book.report("e1", "slayer", 5, 10)
        book.report("e1", "slayer", 5, 10)
        self.assertEqual(book.progress_of("slayer"), 5)
        self.assertFalse(book.is_done("slayer"))

    def test_duplicate_event_id_different_amount_ignored(self):
        book = Achievements()
        book.report("e1", "slayer", 3, 10)
        book.report("e1", "slayer", 999, 10)
        self.assertEqual(book.progress_of("slayer"), 3)

    def test_replaying_whole_sequence_is_stable(self):
        sequence = [
            ("e1", "a", 4, 10),
            ("e2", "a", 4, 10),
            ("e3", "b", 20, 10),
            ("e1", "a", 4, 10),
        ]
        first = Achievements()
        for event in sequence:
            first.report(*event)
        second = Achievements()
        for event in sequence * 3:
            second.report(*event)
        for name in ("a", "b"):
            self.assertEqual(first.progress_of(name), second.progress_of(name))
            self.assertEqual(first.is_done(name), second.is_done(name))


class CapTest(unittest.TestCase):
    def test_progress_is_capped_at_target(self):
        book = Achievements()
        progress = book.report("e1", "slayer", 20, 10)
        self.assertEqual(progress, 10)
        self.assertEqual(book.progress_of("slayer"), 10)
        self.assertTrue(book.is_done("slayer"))

    def test_invariant_progress_never_exceeds_target(self):
        book = Achievements()
        book.report("e1", "slayer", 6, 10)
        book.report("e2", "slayer", 7, 10)
        self.assertLessEqual(book.progress_of("slayer"), 10)
        self.assertEqual(book.progress_of("slayer"), 10)
        self.assertTrue(book.is_done("slayer"))


class DoneTest(unittest.TestCase):
    def test_exactly_at_target_is_done(self):
        book = Achievements()
        book.report("e1", "slayer", 10, 10)
        self.assertTrue(book.is_done("slayer"))

    def test_done_is_irreversible(self):
        book = Achievements()
        book.report("e1", "slayer", 10, 10)
        self.assertTrue(book.is_done("slayer"))
        book.report("e2", "slayer", 0, 10)
        self.assertTrue(book.is_done("slayer"))


class ScanCostTest(unittest.TestCase):
    def test_scanned_does_not_grow_with_achievement_count(self):
        book = Achievements()
        for index in range(3000):
            book.report("e-%d" % index, "a-%d" % index, 1, 100)
        for _ in range(3000):
            book.progress_of("a-2999")
        self.assertLessEqual(book.scanned_count(), 3000)

    def test_query_is_amortized_constant(self):
        small = Achievements()
        large = Achievements()
        for index in range(100):
            small.report("e-%d" % index, "a-%d" % index, 1, 100)
        for index in range(10000):
            large.report("e-%d" % index, "a-%d" % index, 1, 100)
        small.progress_of("a-0")
        large.progress_of("a-0")
        self.assertEqual(small.scanned_count(), large.scanned_count())


class ReferenceImplementation:
    """参考实现：幂等 + 封顶 + 不小于达标，独立朴素写法。"""

    def __init__(self):
        self._seen = set()
        self._progress = {}
        self._targets = {}
        self._done = set()

    def report(self, event_id, name, amount, target):
        if event_id in self._seen:
            return
        self._seen.add(event_id)
        value = self._progress.get(name, 0) + amount
        if value > target:
            value = target
        self._progress[name] = value
        self._targets[name] = target
        if not (value < target):
            self._done.add(name)

    def progress_of(self, name):
        return self._progress.get(name, 0)

    def is_done(self, name):
        return name in self._done


class DifferentialTest(unittest.TestCase):
    def test_random_streams_match_reference(self):
        import random

        rng = random.Random(20261001)
        for _ in range(200):
            book = Achievements()
            reference = ReferenceImplementation()
            names = ["n-%d" % i for i in range(rng.randint(1, 8))]
            event_ids = ["ev-%d" % i for i in range(rng.randint(1, 20))]
            operations = rng.randint(1, 80)
            for _ in range(operations):
                event_id = rng.choice(event_ids)
                name = rng.choice(names)
                amount = rng.randint(0, 25)
                target = rng.choice((1, 5, 10, 20, 50))
                book.report(event_id, name, amount, target)
                reference.report(event_id, name, amount, target)
            for name in names:
                self.assertEqual(
                    book.progress_of(name),
                    reference.progress_of(name),
                    "progress mismatch for %r" % (name,),
                )
                self.assertEqual(
                    book.is_done(name),
                    reference.is_done(name),
                    "done mismatch for %r" % (name,),
                )
                if name in reference._targets:
                    self.assertLessEqual(
                        book.progress_of(name), reference._targets[name]
                    )
