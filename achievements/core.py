"""成就进度：按事件增量更新，重复上报幂等，进度封顶，达标用不小于判定。

口径：
- 同一 ``event_id`` 全局只计一次，重复上报不改变任何状态。
- 单次增量若越过 ``target``，进度封顶在 ``target``，超出部分不累计。
- ``progress >= target`` 即达成；达成不可逆。
"""


class Achievements:
    """成就台账。

    所有操作均为字典/集合的摊还 O(1)，内存 O(成就数 + 事件数)。
    """

    def __init__(self):
        self.progress = {}
        self.done = set()
        self.targets = {}
        self.handled = set()
        self.scanned = 0

    def report(self, event_id, name, amount=1, target=None):
        """上报一次进度增量。

        幂等：相同 ``event_id`` 的重复上报整体忽略。同一成就的 ``target``
        以首次上报为准，后续上报不再改变它（``target`` 省略时沿用旧值）。
        进度在 ``target`` 处封顶，``progress >= target`` 时标记达成。
        """
        if event_id in self.handled:
            return self.progress.get(name, 0)
        self.handled.add(event_id)

        if target is None:
            target = self.targets.get(name)
        else:
            target = self.targets.setdefault(name, target)

        current = self.progress.get(name, 0) + amount
        if target is not None and current > target:
            current = target
        self.progress[name] = current

        if target is not None and current >= target:
            self.done.add(name)
        return current

    def progress_of(self, name):
        """当前进度。哈希直查，单次摊还 O(1)，不随成就数扫描。"""
        self.scanned += 1
        return self.progress.get(name, 0)

    def is_done(self, name):
        return name in self.done

    def scanned_count(self):
        return self.scanned
