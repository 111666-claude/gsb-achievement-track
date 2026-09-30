"""成就进度：按事件增量更新，重复上报幂等，进度封顶，达标用不小于判定。

口径（README 为准）：
- 事件幂等：同一个 event_id 只计一次。
- 进度封顶：进度最多等于 target，超出部分不再累计。
- 达标用不小于：进度等于 target 即达成；达成不可逆。
- 查询代价：progress_of 单次 O(1)，scanned_count 只统计实际查询次数，
  不随成就数线性增长。
"""


class Achievements:
    """成就台账。"""

    def __init__(self):
        self.progress = {}
        self.done = set()
        self.targets = {}
        self.handled = set()
        self.scanned = 0

    def report(self, event_id, name, amount, target):
        """上报一次进度增量。

        同一 event_id 只计一次；进度封顶在 target；达到 target 即达成，
        且达成状态不可逆。
        """
        if event_id in self.handled:
            return self.progress.get(name, 0)
        self.handled.add(event_id)

        current = self.progress.get(name, 0)
        current = min(target, current + amount)
        self.progress[name] = current
        self.targets[name] = target
        if current >= target:
            self.done.add(name)
        return current

    def progress_of(self, name):
        """当前进度：直接字典查表，单次 O(1)。"""
        self.scanned += 1
        return self.progress.get(name, 0)

    def is_done(self, name):
        return name in self.done

    def scanned_count(self):
        return self.scanned
