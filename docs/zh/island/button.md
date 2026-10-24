# button：按钮

![button](../../images/island/button.svg)

只能放在展开时。左边的按钮只有图标，右边的有图标也有字。

```json
{ "type": "button", "id": "pause", "icon": "Pause" }
```

```json
{ "type": "button", "id": "skip", "icon": "SkipForward", "text": "跳过" }
```

| 字段 | 必须有吗 | 说明 |
|---|---|---|
| `id` | 是 | 插件自己起的名字，被点时原样交回给插件 |
| `icon` | 是 | 图标的名字，和 [`icon`](icon.md) 的 `name` 一样 |
| `text` | 否 | 按钮上的字 |

按钮被点时，后台脚本收到 `island.clicked` 事件，内容是 `{ "button": "<id>" }`。点按钮不会打开插件的页面。

```js
hindsight.on("island.clicked", ({ button }) => {
  if (button === "pause") {
    // 暂停
  }
});
```

只有后台运行的插件能放按钮：没有后台脚本，就收不到点击，`island.show` 会报错。

## 允许的放置位置

- `open.left`、`open.right`。

## 长度限制

- `id` 最长 64 字节，不能是空的。
- `text` 最多 20 宽，宽度的算法见 [text](text.md)。不能是空的，也不能有换行这类控制字符。
