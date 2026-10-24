# ring：进度环

![ring](../../images/island/ring.svg)

左边是收起时，右边是展开时，`value` 都是 0.75。

```json
{ "type": "ring", "value": 0.75, "text": "75%", "color": "#34d399" }
```

| 字段 | 必须有吗 | 说明 |
|---|---|---|
| `value` | 是 | 0 到 1 的进度。1 是画满一圈 |
| `text` | 否 | 收起时在环的右边，展开时在环的中间 |
| `color` | 否 | 环的颜色，`#rrggbb`，不给是白色 |

## 允许的放置位置

| 位置 | 样子 |
|---|---|
| `closed.left`、`closed.right` | 14 像素的环 |
| `open.left`、`open.right` | 52 像素的环 |

## 长度和取值限制

不合就报错：

- `value` 在 0 到 1 之间。
- `text` 最多 6 宽，宽度的算法见 [text](text.md)。不能是空的，也不能有换行这类控制字符。
