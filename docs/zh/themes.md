# 写一个 Hindsight 主题

主题改变 Hindsight 的样子。一个主题是一个文件夹，里面有两个文件：

| 文件 | 必须有 | 做什么 |
|---|---|---|
| `theme.json` | 是 | 选布局和明暗，设置公开的 CSS 变量 |
| `theme.css` | 否 | 其他任何 CSS，能改主窗口里的任何东西 |

[`theme.schema.json`](https://github.com/Tomotsugu-dev/Hindsight/blob/main/docs/design/themes/theme.schema.json) 描述 `theme.json` 的格式。[`example/`](https://github.com/Tomotsugu-dev/Hindsight/tree/main/docs/design/themes/example) 是一个完整的主题。主题要 Hindsight 0.10.2 或更新的版本。

## 安装主题

在 Hindsight 里打开「设置 → 外观 → 自定义主题」。

- **获取主题**：在浏览器里打开[主题网站](https://hindsight.kyosweb.com/themes/)。在那里下载主题、解压，再导入。
- **导入主题**：选主题的 `theme.json`。同一个文件夹里有 `theme.css` 的话，也一起导入。id 相同的主题会被替换。
- **打开主题文件夹**：把主题的文件夹拷进去。文件夹名必须是主题的 id。

主题文件夹是数据文件夹里的 `themes/`。默认位置：macOS 是 `~/Library/Application Support/Hindsight/themes/`，Windows 是 `%APPDATA%\Hindsight\themes\`。

每次切回 Hindsight，它都会重新读主题文件夹。改的是正在用的主题时，窗口这时就显示改动。做主题最快的办法：直接改主题文件夹里的文件，再切回 Hindsight。

读不了的主题也会列出来，并写明原因。正在用的主题坏了或被删了，Hindsight 先显示「简约」，等主题修好再换回来。

## theme.json

```json
{
  "$schema": "https://raw.githubusercontent.com/Tomotsugu-dev/Hindsight/main/docs/design/themes/theme.schema.json",
  "format": 1,
  "id": "harbor",
  "name": "Harbor",
  "version": "1.0.0",
  "author": "Hindsight",
  "description": { "en": "Slate blue on cool grey.", "zh-CN": "冷灰底色，石板蓝点缀。" },
  "layout": "card",
  "mode": "light",
  "tokens": {
    "--color-accent": "#3b6e8f",
    "--color-accent-soft": "rgba(59, 110, 143, 0.12)"
  }
}
```

| 字段 | 必须有 | 规则 |
|---|---|---|
| `format` | 是 | `1` |
| `id` | 是 | 小写字母、数字和 `-`，1 到 63 个字符，不能以 `-` 开头或结尾。必须和文件夹名一样 |
| `name` | 是 | 最多 64 个字符，不能只有空格 |
| `version` | 是 | 三个数字，比如 `1.0.0` |
| `author` | 否 | 最多 64 个字符 |
| `description` | 否 | 语言代码 → 文字，比如 `"en"`、`"zh-CN"`、`"zh-TW"`、`"ja"`、`"es"`、`"pt-BR"`。Hindsight 先显示界面语言的，没有就显示 `en`，再没有就按代码排序显示第一种 |
| `layout` | 否 | `card`（默认）或 `flat`。`flat` 去掉卡片的阴影，圆角更小，文字更细 |
| `mode` | 否 | `light`（默认）或 `dark`。图表跟着它变 |
| `tokens` | 否 | 公开变量 → CSS 值，见下文 |
| `$schema` | 否 | 让编辑器检查这个文件。Hindsight 不读它 |

Hindsight 不认识的字段会被忽略。新版本的 Hindsight 可以加字段，旧版本照样能用这个主题。

### 公开变量

主题从「明亮」主题的颜色开始；写了 `"mode": "dark"` 的，从「暗色」主题的颜色开始。然后 `tokens` 改掉它写到的变量。默认值见 [`src/styles/tokens.css`](https://github.com/Tomotsugu-dev/Hindsight/blob/main/src/styles/tokens.css)。

| 分组 | 变量 |
|---|---|
| 强调色 | `--color-accent`、`--color-accent-soft`（浅色的强调背景，比如选中项） |
| 侧栏 | `--sidebar-gradient`（任意 CSS 背景）、`--sidebar-border` |
| 底色 | `--surface-app`（页面）、`--surface-card`、`--surface-card-elevated`、`--surface-overlay`（菜单和对话框）、`--surface-1`、`--surface-2` |
| 侧栏里的选中项 | `--pill-bg`、`--pill-blur`（`backdrop-filter` 的值）、`--pill-shadow`、`--text-on-pill` |
| 悬停 | `--hover-bg` |
| 文字 | `--text-strong`、`--text-regular`、`--text-muted`、`--text-faint` |
| 状态 | `--status-ok`、`--status-pending`、`--status-idle`、`--status-error`、`--status-ok-soft`、`--status-error-soft`、`--status-pending-soft` |
| 边框 | `--border-subtle`、`--border-default`、`--border-strong`、`--hairline-hi`（卡片和按钮上沿那条细细的亮线） |
| 控件 | `--control-bg`、`--control-bg-hover`（菜单和日期按钮） |
| 滚动条 | `--scrollbar-thumb`、`--scrollbar-thumb-hover` |
| 阴影 | `--shadow-sm`、`--shadow-md`、`--shadow-lg`、`--shadow-inset-hi`、`--shadow-strength` |
| 圆角 | `--radius-xs`、`--radius-sm`、`--radius-md`、`--radius-lg`、`--radius-xl` |
| 字体 | `--font-sans`、`--font-mono`（路径和代码） |

- `--shadow-strength` 是一个数。所有深色阴影的不透明度都乘以它：`0` 去掉阴影，`1` 是默认，`2` 让阴影深一倍。
- `--color-accent-soft` 要和 `--color-accent` 一起设。浅色的强调背景不会自己跟着变。
- 一个值最多 300 个字符，不能只有空格，不能有 `;`、`{`、`}` 或控制字符。
- 不在这张表里的变量不起作用。主题照样能用，设置里这个主题的卡片会列出哪些变量没起作用。

## theme.css

`theme.css` 排在 Hindsight 自己所有的 CSS 后面，所以优先级相同时，它的规则胜过内置的规则。`theme.json` 里的变量又胜过 `theme.css`。

选择器里用下面这些名字，它们不随版本变：

| 选择器 | 是什么 |
|---|---|
| `[data-part="app"]` | 整个窗口 |
| `[data-part="sidebar"]` | 侧栏 |
| `[data-part="nav-item"]` | 侧栏里的一项。当前页面那一项有 `aria-current="page"` |
| `[data-part="content"]` | 侧栏右边的区域 |
| `[data-part="page-header"]` | 页面顶部的标题 |
| `[data-part="tabs"]` | 一排标签页 |
| `[data-part="card"]` | 统计页上的卡片 |
| `[data-part="chart"]` | 图表 |
| `[data-part="ranked-list"]` | 应用排行 |
| `[data-part="drawer"]` | 应用详情的面板 |
| `[data-part="dialog"]` | 对话框 |
| `[data-part="section"]` | 设置页上的一节 |
| `[data-part="row"]` | 一节里的一行 |
| `[data-part="toggle"]` | 开关。打开时有 `aria-checked="true"` |
| `[data-part="slider"]` | 滑块 |

`<html>` 上还有 `data-layout`（`card` 或 `flat`）和 `data-mode`（`light` 或 `dark`），来自 `theme.json`。

不要用类名。类名长得像 `._item_1jwc4_1`，每个版本都会变。别的选择器，比如某个部分里面的元素名，页面一改也可能失效。

主窗口的限制：

- `@import` 会被忽略。所有 CSS 都写在 `theme.css` 里。
- 不能从网上加载字体。也不能从网上加载图片，Hindsight 显示图标用的两个网站除外。字体或图片要写成 `data:` 网址放进 `theme.css`，或者用电脑上装好的字体。
- `theme.json` 最大 64 KB，`theme.css` 最大 512 KB，都必须是 UTF-8。

## 安全

`theme.css` 在主窗口里运行，能隐藏或改掉那里的任何东西。只装信得过的主题；分享给别人的主题，不要从网上加载任何东西。

## 兼容

公开变量和 `data-part` 的名字是一个承诺：Hindsight 不改它们的名字，用它们的主题就一直能用。页面上的其他东西，任何版本都可能变。

## 分享主题

想把主题放到[主题网站](https://hindsight.kyosweb.com/themes/)上，见 CONTRIBUTING.md 的 [Themes](../../CONTRIBUTING.md#themes)（英文）。
