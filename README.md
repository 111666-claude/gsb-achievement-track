# achievement-track

成就进度：按事件增量更新，重复上报幂等，进度封顶，达标用不小于判定，只用 Python 标准库。

```
python3 -m achievements.cli --sample dup
python3 -m achievements.cli --sample cap
python3 -m achievements.cli --sample exact
python3 -m unittest discover -s tests -v
```

## 口径（README 为准）

- **事件幂等**：同一个 `event_id` 只计一次，重复上报不改变进度。
- **进度封顶**：进度最多等于 `target`，超出部分不再累计。
- **达标用不小于**：进度等于 `target` 就算达成（不是大于）。
- **达成不可逆**：已经达成的成就不因后续进度变化而取消。
- **查询代价**：`progress_of` 不许每次全扫所有成就，`scanned_count()` 不随成就数线性增长。
- **规模**：单服 20 万成就、每秒 10 万次上报与查询，单次摊还 O(1)，内存 O(成就数)。

## 输出契约（不改格式）

```
progress=5 done=false
progress=10 done=true
done=true
scanned<=3000
```

## 目录

```
achievements/core.py   进度、幂等与达标
achievements/cli.py    命令行入口
tests/                 unittest 用例
```
