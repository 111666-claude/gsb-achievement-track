"""成就进度：按事件增量更新，重复上报幂等，进度封顶，达标用不小于判定。

缺陷：重复上报重复计数、进度不封顶、达标判定用严格大于、查询每次全扫所有成就。
"""


class Achievements:
    """成就台账。"""

    def __init__(self):
        self.progress = {}
        self.done = set()
        self.handled = {}
        self.scanned = 0

    def report(self, event_id, name, amount, target):
        """上报一次进度增量。缺陷：不去重、不封顶、正好达标不算达成。"""
        self.progress[name] = self.progress.get(name, 0) + amount
        if self.progress[name] > target:
            self.done.add(name)
        return self.progress[name]

    def progress_of(self, name):
        """当前进度。缺陷：每次全扫所有成就。"""
        self.scanned += len(self.progress)
        return self.progress.get(name, 0)

    def is_done(self, name):
        return name in self.done

    def scanned_count(self):
        return self.scanned
