# 权限

插件在 manifest 的 `permissions` 里列出要的权限。安装时，用户看到每个权限做什么，勾选同意了才能装。

插件要 Hindsight 0.10.0 或更新的版本。这一页的权限都从 0.10.0 开始有，以后新加的会写明从哪个版本开始。

## 全部权限

### 读统计

| 权限 | 允许做什么 | 要和谁一起申请 |
|---|---|---|
| `stats.read` | 用 [`stats.day_by_category`](api.md#statsday_by_category) 读每个分类每天用了多久。不含窗口标题、网址 | 至少一档范围 |
| `stats.today` | 读今天 | `stats.read` |
| `stats.week` | 读本周一到今天 | `stats.read` |
| `stats.month` | 读本月 1 号到今天，加上本周 | `stats.read` |
| `stats.history` | 读所有日子 | `stats.read` |
| `devices.read` | `stats.day_by_category` 按主窗口里选的设备算。没有它只算这台电脑 | |
| `categories.read` | 用 [`categories.list`](api.md#categorieslist) 列出全部分类 | |
| `super_categories.read` | 用 [`super_categories.list`](api.md#super_categorieslist) 列出全部大类 | |

- 四档范围里，宽的一档包含窄的。
- 有 `stats.read` 却没有范围，manifest 通不过检查。这样用户安装时一定看得到插件能往回读多久。

### 收焦点事件

| 权限 | 允许做什么 | 要和谁一起申请 |
|---|---|---|
| `focus.changed` | 收 [`focus.changed`](api.md#focuschanged) 事件。事件里只有 `at` 和 `away` | manifest 里 `runs_in_background` 是 `true` |
| `focus.app` | 事件里加上应用名 | `focus.changed` |
| `focus.category` | 事件里加上分类 | `focus.changed` |
| `focus.title` | 事件里加上窗口标题和网站域名 | `focus.changed` |

### 系统功能

| 权限 | 允许做什么 | 要和谁一起申请 |
|---|---|---|
| `notifications` | 用 [`notifications.send`](api.md#notificationssend) 发系统通知 | |
| `notifications.sound` | 通知带上系统提示音。从 0.10.1 开始有 | `notifications` |
| `island` | 用 `island.show`、`island.hide` 在岛上放内容、撤下，见 [岛](island.md) | |

## 不要权限的

- 读写插件自己的数据库。但 manifest 里要写 `storage_mb`，没有就报 `plugin has no permission: storage_mb`。见 [db.execute、db.query](api.md#dbexecutedbquery)。
- `window.changed` 事件：只发给这个插件，说的是它自己的窗口。
- `island.clicked` 事件：只有在岛上放了按钮的插件收得到，放按钮已经要 `island`。

## 检查

manifest 通不过检查就装不上：

| 什么时候 | 报错 |
|---|---|
| 这个版本的 Hindsight 不认识这个权限 | `plugin unknown permission: <权限名>` |
| 少了「要和谁一起申请」里的那个 | `plugin manifest: <权限名> needs <它要的权限>` |
| 有 `stats.read` 却没有范围 | `plugin manifest: stats.read needs one of stats.today, stats.week, stats.month, stats.history` |
| 有 `focus.changed`，`runs_in_background` 却不是 `true` | `plugin manifest: focus.changed needs runs_in_background` |

- 用了新版本才有的权限，在旧版 Hindsight 上装不上，用户要先更新 Hindsight。比如要 `notifications.sound` 的插件，在 0.10.0 上装不上。
- 调用方法时缺权限，`hindsight.call()` 返回的 Promise reject，message 是 `plugin has no permission: <权限名>`。

## 安装时用户看到什么

- 插件要的每个权限，一行说明。`focus.title` 标成「高风险」。
- 有 `storage_mb` 时，最多占多少 MB 磁盘。
- 从文件安装、`runs_in_background` 是 `true` 时，一行「后台运行的权限」。从插件市场安装时不显示这一行。
- 一个勾选框。勾上才能装。
- 不是官方的插件，还会提醒「此插件有可能造成个人信息泄漏等后果」。从文件安装的插件都算不是官方的。

什么都不要的插件，显示「这个插件不读取你的任何数据。」

## 什么权限都给不了的

- 联网。见 [插件不能做什么](getting-started.md#插件不能做什么)。
- 截图、AI 报告和聊天记录。
- 完整的网址。`focus.title` 只给域名。
