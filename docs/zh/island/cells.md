# cells：格子

![cells](../../images/island/cells.svg)

只能放在展开时。图里每行 10 格，一共 14 格，第 8 格是当前那格。比如专注插件今天每段专注一格，颜色是那段的分类。

```json
{
  "type": "cells",
  "colors": ["#a78bfa", "#a78bfa", "#a78bfa", "#a78bfa", "#a78bfa", "#f87171", "#a78bfa", "#a78bfa", null, null, null, null, null, null],
  "columns": 10,
  "current": 7
}
```

| 字段 | 必须有吗 | 说明 |
|---|---|---|
| `colors` | 是 | 每格一个颜色，`#rrggbb`；空格子是 `null` |
| `columns` | 是 | 每行几格 |
| `current` | 否 | 当前那格的下标，从 0 数。这一格有白框 |

- 格子最大 10 像素。岛上放不下时，格子会变小。

## 允许的放置位置

- `open.left`、`open.right`。

## 数量限制

不合就报错：

- `columns` 是 1 到 20。
- 最多 3 行，所以 `colors` 最多 60 个。`colors` 不能是空的。
- `current` 要落在格子里。
