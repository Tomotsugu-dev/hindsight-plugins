# 岛

岛在 macOS 菜单栏的正中间。插件可以在上面放一点内容，比如还剩多少专注时间。鼠标移上去，岛会展开；点一下，打开插件的页面。

- 要 `island` 权限，见 [权限](permissions.md)。
- 只有 macOS 有岛。在别的系统上，`island.show` 照样成功，只是什么都不显示。
- 插件只说哪块地方放什么组件，岛由 Hindsight 来画。插件不能放自己的 HTML。

## 岛上的几块地方

### 收起时

![收起的岛](../images/island-closed.svg)

上面是有刘海的屏幕，下面是没有刘海的屏幕。

| 位置 | 能放什么 |
|---|---|
| `closed.left` | 一个 [`icon`](island/icon.md)、[`timer`](island/timer.md)、[`ring`](island/ring.md) 或 [`text`](island/text.md) |
| `closed.right` | 同上 |

- 左右两边至少放一边。没放的一边不伸出来。
- 每边的宽度跟着内容，最宽 90 像素。只放一个图标时是圆的。
- 收起时只有菜单栏那么高，所以这里的 `text` 只能是小字，不能带 `sub`。

### 展开时

![展开的岛](../images/island-open.svg)

| 位置 | 能放什么 |
|---|---|
| `closed.left` | 留在原处，和收起时一样 |
| `open.topRight` | 一段小字的 [`text`](island/text.md)。有刘海时在刘海右边，没有刘海时紧跟在 `closed.left` 后面。有它时 `closed.right` 不显示，没它时 `closed.right` 留在原处 |
| `open.left` | 最多 3 个组件，从上往下排，靠左 |
| `open.right` | 最多 2 个组件，排成一行，靠右 |
| `open.bottomRight` | 一段小字的 [`text`](island/text.md)，在 `open.right` 下面，靠右 |

- 展开的岛宽高都跟着内容，最宽 520 像素。
- `open` 可以不给。不给时鼠标移上去不展开，点一下照样打开插件的页面。

## 一个例子

专注插件开始一段 25 分钟的专注：

```json
{
  "closed": {
    "left": { "type": "icon", "name": "Code", "color": "#a78bfa" },
    "right": { "type": "timer", "start": "2026-10-21T10:00:00+09:00", "end": "2026-10-21T10:25:00+09:00", "color": "#fb923c" }
  },
  "open": {
    "topRight": { "type": "text", "text": [{ "text": "工作中", "bold": true }, { "text": " · Code", "dim": true }] },
    "left": [
      { "type": "text", "text": [{ "text": "2:40", "bold": true }], "sub": "/ 6:00", "size": "large" },
      { "type": "cells", "colors": ["#a78bfa", "#a78bfa", "#f87171", null, null], "current": 2, "columns": 15 }
    ],
    "right": [
      { "type": "timer", "start": "2026-10-21T10:00:00+09:00", "end": "2026-10-21T10:25:00+09:00", "color": "#fb923c" },
      { "type": "button", "id": "pause", "icon": "Pause" }
    ],
    "bottomRight": { "type": "text", "text": ["分心 ", { "text": "3", "color": "#f87171", "bold": true }, " 次"] }
  }
}
```

对着上面两张图看：

- 收起时：左边是分类图标，右边是倒计时。
- 展开时：最上面一条右边是「工作中 · Code」；左边一列是今天做了多久和一排格子；右边一行是倒计时和暂停按钮；按钮下面是分心次数。

放上去和撤下来：

```js
hindsight.call("island.show", content);
hindsight.call("island.hide");
```

## 组件

每个组件一页，字段、允许的放置位置、限制都在里面。

| 组件 | 是什么 | 收起时能放吗 |
|---|---|---|
| [`icon`](island/icon.md) | 图标 | 能 |
| [`text`](island/text.md) | 一行字 | 能，只能是小字 |
| [`timer`](island/timer.md) | 倒计时 | 能 |
| [`ring`](island/ring.md) | 进度环 | 能 |
| [`cells`](island/cells.md) | 格子 | 不能 |
| [`button`](island/button.md) | 按钮 | 不能 |

所有组件的颜色都一样：

- 只能是 `#rrggbb`。
- 太暗的颜色由 Hindsight 调亮，让它在黑底上看得清。插件可以直接用分类的颜色。

## 报错

- 超过上限或者不合规则，`island.show` 就报错，不会悄悄截掉。每个组件的上限写在它那页。
- 报错的消息以 `invalid input: ` 开头。哪块地方或哪个组件出错，后面就是它的位置，比如 `invalid input: open.left[1]: text is 9 wide, at most 8`。

## 几个插件都要用岛

- 后调用 `island.show` 的插件占着岛。它调 `island.hide` 以后，前一个还没撤下的插件回到岛上。
- 插件被关掉、卸载，或者后台脚本被停掉，它放的内容就撤下。
- 点岛打开的是现在占着岛的插件的页面，在单独的窗口里打开。

## 新旧版本

- 岛从 Hindsight 0.10.0 开始有。
- 不认识的组件跳过，不报错：新插件用了新组件，在旧版 Hindsight 上只少显示一块。只有收起时两边都被跳过才报错，因为岛上什么都没有了。
- 跳过的组件照样算在 `open.left`、`open.right` 的个数里。同样的内容，在新旧版本上要么都报错，要么都不报错。
- 不认识的字段忽略。
