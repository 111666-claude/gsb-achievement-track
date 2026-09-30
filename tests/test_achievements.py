import random
import unittest

from achievements.core import Achievements


class IdempotencyTest(unittest.TestCase):
    def test_duplicate_event_counts_once(self):
        book = Achievements()
        self.assertEqual(book.report("e1", "slayer", 5, 10), 5)
        self.assertEqual(book.report("e1", "slayer", 5, 10), 5)
        self.assertEqual(book.progress_of("slayer"), 5)
        self.assertFalse(book.is_done("slayer"))

    def test_duplicate_event_ignored_for_different_name(self):
        # 同一 event_id 的重复上报整体忽略，即使附带的成就名不同。
        book = Achievements()
        book.report("e1", "a", 1, 10)
        book.report("e1", "b", 9, 10)
        self.assertEqual(book.progress_of("a"), 1)
        self.assertEqual(book.progress_of("b"), 0)

    def test_replaying_same_sequence_is_deterministic(self):
        events = [
            ("e1", "a", 5, 10),
            ("e2", "a", 5, 10),
            ("e1", "a", 5, 10),
            ("e3", "a", 20, 10),
            ("e4", "b", 10, 10),
        ]

        first = Achievements()
        for event in events:
            first.report(*event)

        second = Achievements()
        for event in events:
            second.report(*event)

        for name in ("a", "b"):
            self.assertEqual(first.progress_of(name), second.progress_of(name))
            self.assertEqual(first.is_done(name), second.is_done(name))


class CapTest(unittest.TestCase):
    def test_progress_capped_at_target(self):
        book = Achievements()
        progress = book.report("e1", "slayer", 20, 10)
        self.assertEqual(progress, 10)
        self.assertEqual(book.progress_of("slayer"), 10)
        self.assertTrue(book.is_done("slayer"))

    def test_excess_does_not_accumulate_after_cap(self):
        book = Achievements()
        book.report("e1", "a", 8, 10)
        book.report("e2", "a", 8, 10)  # 16 -> 封顶 10
        self.assertEqual(book.progress_of("a"), 10)

    def test_duplicate_after_cap_changes_nothing(self):
        book = Achievements()
        book.report("e1", "a", 20, 10)
        self.assertEqual(book.report("e1", "a", 20, 10), 10)
        self.assertEqual(book.progress_of("a"), 10)


class DoneTest(unittest.TestCase):
    def test_exactly_at_target_is_done(self):
        book = Achievements()
        self.assertEqual(book.report("e1", "slayer", 10, 10), 10)
        self.assertTrue(book.is_done("slayer"))

    def test_exactly_at_target_across_events(self):
        book = Achievements()
        book.report("e1", "a", 4, 10)
        book.report("e2", "a", 6, 10)
        self.assertEqual(book.progress_of("a"), 10)
        self.assertTrue(book.is_done("a"))

    def test_done_is_irreversible(self):
        book = Achievements()
        book.report("e1", "a", 10, 10)
        self.assertTrue(book.is_done("a"))
        book.report("e2", "a", 0, 10)
        self.assertTrue(book.is_done("a"))


class QueryCostTest(unittest.TestCase):
    def test_scanned_does_not_grow_with_achievement_count(self):
        book = Achievements()
        for index in range(3000):
            book.report("e-%d" % index, "a-%d" % index, 1, 100)
        before = book.scanned_count()
        for _ in range(3000):
            book.progress_of("a-2999")
        self.assertEqual(book.scanned_count() - before, 3000)
        self.assertLessEqual(book.scanned_count(), 3000 + before)

    def test_scanned_constant_per_query_at_scale(self):
        book = Achievements()
        for index in range(200000):
            book.report("e-%d" % index, "a-%d" % index, 1, 100)
        start = book.scanned_count()
        book.progress_of("a-0")
        book.progress_of("a-199999")
        book.progress_of("missing")
        self.assertEqual(book.scanned_count() - start, 3)


def _reference_replay(events, queries):
    """独立参考实现：全局 event_id 去重 + target 封顶 + >= 达标。"""
    progress = {}
    targets = {}
    done = set()
    seen = set()
    for event_id, name, amount, target in events:
        if event_id in seen:
            continue
        seen.add(event_id)
        targets.setdefault(name, target)
        value = min(progress.get(name, 0) + amount, targets[name])
        progress[name] = value
        if value >= targets[name]:
            done.add(name)
    return [
        (progress.get(name, 0), name in done)
        for name in queries
    ]


class DifferentialTest(unittest.TestCase):
    def test_random_streams_match_reference(self):
        rng = random.Random(20261001)
        for case in range(200):
            name_count = rng.randint(1, 12)
            names = ["a%d" % i for i in range(name_count)]
            targets = {name: rng.randint(1, 15) for name in names}

            events = []
            unique_events = rng.randint(1, 40)
            for index in range(unique_events):
                name = rng.choice(names)
                # 允许超量上报（amount 远大于 target）。
                amount = rng.randint(0, targets[name] * 3)
                events.append(("ev%d" % index, name, amount, targets[name]))
            # 插入重复 event_id（可能携带不同 amount/name）。
            duplicates = rng.sample(events, rng.randint(0, len(events)))
            for event in duplicates:
                # 重发即同一事件的原样副本（同 name/amount/target）。
                events.insert(rng.randrange(len(events) + 1), event)
            rng.shuffle(events)

            queries = [rng.choice(names) for _ in range(rng.randint(1, 30))]
            queries.append("never-reported")

            book = Achievements()
            for event in events:
                book.report(*event)
            actual = [(book.progress_of(name), book.is_done(name)) for name in queries]

            expected = _reference_replay(events, queries)
            self.assertEqual(actual, expected, "case %d 与参考实现不一致" % case)

            # 不变量：progress 永远不大于 target；重复执行整串结果相同。
            for name in names:
                self.assertLessEqual(book.progress_of(name), targets[name])
            replayed = Achievements()
            for event in events:
                replayed.report(*event)
            for name in queries:
                self.assertEqual(replayed.progress_of(name), book.progress_of(name))
                self.assertEqual(replayed.is_done(name), book.is_done(name))


if __name__ == "__main__":
    unittest.main()
