# 接口参考

插件要 Hindsight 0.10.0 或更新的版本。这一页的全部内容都从 0.10.0 开始有，以后新加的会写明从哪个版本开始。

## manifest.json

```json
{
  "id": "welcome-back",
  "name": "欢迎回来",
  "version": "0.1.0",
  "permissions": ["focus.changed", "notifications", "stats.read", "stats.today"],
  "runs_in_background": true,
  "storage_mb": 1,
  "opens_in": "window",
  "window": { "width": 360, "height": 480 }
}
```

| 字段 | 必须有吗 | 说明 |
|---|---|---|
| `id` | 是 | 小写字母、数字和 `-`，不能以 `-` 开头或结尾，最长 63 个字符。插件市场里不能重名 |
| `name` | 是 | 给用户看的名字，不能是空的。通知的标题也用它 |
| `version` | 是 | 三段数字，比如 `0.1.0`。不能写成 `v0.1.0` 或 `0.1.0-beta` |
| `permissions` | 是 | 要的权限，见 [权限](permissions.md)。不要权限就写 `[]` |
| `runs_in_background` | 是 | `true` 时，Hindsight 开着就一直运行 `background.js` |
| `storage_mb` | 否 | 插件自己的数据库最多占多少 MB，1 到 10240。不写就不能用 `db.execute`、`db.query` |
| `opens_in` | 否 | 页面默认在哪打开：`"main"` 在主窗口的侧栏里，`"window"` 在单独的窗口里。不写时侧栏里没有它，用户从设置里打开，在单独的窗口里。用户可以在设置里改 |
| `window` | 否 | 页面第一次在单独的窗口里打开时的大小。每边至少 200，最大 2560×1440。不写是 900×640 |

- 不认识的字段忽略。
- 安装时，用户看到 `permissions` 和 `storage_mb`，同意了才能装，见 [安装时用户看到什么](permissions.md#安装时用户看到什么)。

## 包

| 文件 | 说明 |
|---|---|
| `manifest.json` | 必须有，最大 64 KB |
| `background.js` | `runs_in_background` 是 `true` 时必须有 |
| `ui/index.html` | 有它才有页面 |
| `icon.png` | 可以没有，没有就用默认图标。PNG，最大 256 KB |

- 这些文件在 zip 的最上层。
- zip 里最多 1000 个文件，解开后最大 100 MB。
- `background.js` 在 Worker 里作为普通脚本运行，不是 ES 模块，不能写 `import`。要拆成几个文件，用 `importScripts("lib.js")`，路径从包的最上层算。

## 调用方法和收事件

| | 后台脚本 | 页面 |
|---|---|---|
| 调方法 | `hindsight.call(method, params)` | 先加载 `../_page.js`，再 `hindsight.call(method, params)` |
| 收事件 | `hindsight.on(name, callback)` | 收不到 |

`hindsight.call()` 返回一个 Promise。失败时 reject 一个 `Error`，message 写着原因：

| 什么时候 | message |
|---|---|
| 插件被关掉了 | `plugin not enabled: <插件 id>` |
| 没有这个方法 | `plugin unknown method: <方法名>` |
| 缺权限 | `plugin has no permission: <权限名>` |
| 参数不对 | `invalid input: …` |

## 方法

每个权限允许做什么，见 [权限](permissions.md)。

| 方法 | 要的权限 | 做什么 |
|---|---|---|
| `stats.day_by_category` | `stats.read` 加一档范围 | 某一天各分类用了多久 |
| `categories.list` | `categories.read` | 列出全部分类 |
| `super_categories.list` | `super_categories.read` | 列出全部大类 |
| `notifications.send` | `notifications`，带提示音还要 `notifications.sound` | 发系统通知 |
| `db.execute`、`db.query` | 不要权限，要 `storage_mb` | 读写插件自己的数据库 |
| `island.show`、`island.hide` | `island` | 在岛上放内容、撤下，见 [岛](island.md) |

### stats.day_by_category

```js
hindsight.call("stats.day_by_category", { date: "2026-10-22" });
```

| 参数 | 必须有吗 | 说明 |
|---|---|---|
| `date` | 是 | `YYYY-MM-DD`，按本机的日期。不能是明天以后 |
| `devices` | 否 | `"this"`（默认）只算这台电脑；`"selected"` 按主窗口里选的设备算，要 `devices.read` |

返回这一天用过的分类，用时多的在前：

```json
[
  {
    "id": "code",
    "name": "Coding",
    "color": "#a78bfa",
    "icon": "Code",
    "seconds": 12600,
    "superCategory": { "id": "work", "name": "Work", "color": "#8b5cf6", "icon": "Briefcase" }
  }
]
```

- 没归入大类的分类，`superCategory` 是 `null`。
- 大类的时长由插件自己按 `superCategory` 加起来。

能读哪些日子，看插件有哪一档范围：

| 权限 | 能读 |
|---|---|
| `stats.today` | 今天 |
| `stats.week` | 本周一到今天 |
| `stats.month` | 本月 1 号到今天，加上本周 |
| `stats.history` | 所有日子 |

- 宽的一档包含窄的。
- 读不到这一天时，报错里是能读到这天的那一档，比如 `plugin has no permission: stats.week`。

### categories.list

```js
hindsight.call("categories.list");
```

返回全部分类，顺序和主窗口一样。格式和 `stats.day_by_category` 的一项一样，只是没有 `seconds`。

`stats.day_by_category` 只返回那天用过的分类。插件的设置页要让用户从全部分类里挑时，用这个方法。

### super_categories.list

```js
hindsight.call("super_categories.list");
```

返回全部大类，顺序和主窗口一样：

```json
[{ "id": "work", "name": "Work", "color": "#8b5cf6", "icon": "Briefcase" }]
```

### notifications.send

```js
hindsight.call("notifications.send", { body: "已经看了 10 分钟 YouTube" });
hindsight.call("notifications.send", { body: "这一段结束了", sound: true });
```

| 参数 | 必须有吗 | 说明 |
|---|---|---|
| `body` | 是 | 通知的正文，不能是空的 |
| `sound` | 否 | `true` 时同时播放系统提示音，要 `notifications.sound`。从 0.10.1 开始有 |

- 标题固定是插件的 `name`。
- 不带 `sound` 时，通知没有声音。
- `sound` 是 `true` 却没有 `notifications.sound` 时报错，通知也不发。
- 只能播系统默认的提示音，换不了别的声音。
- 不限频率。发得太多，用户会把插件关掉。

### db.execute、db.query

每个插件有自己的一个 SQLite 数据库，别的插件读不到。

- 更新插件时，数据还在。卸载时，用户选删不删。
- 不同步到用户的其他设备。
- 要在 manifest 里写 `storage_mb`，用户安装时同意。没有就报 `plugin has no permission: storage_mb`。

```js
hindsight.call("db.execute", {
  sql: "CREATE TABLE IF NOT EXISTS pomodoro (date TEXT, minutes INTEGER)",
});
hindsight.call("db.execute", {
  sql: "INSERT INTO pomodoro VALUES (?, ?)",
  params: ["2026-10-22", 25],
});
hindsight.call("db.query", { sql: "SELECT date, minutes FROM pomodoro" });
```

| 参数 | 必须有吗 | 说明 |
|---|---|---|
| `sql` | 是 | 一条 SQL 语句 |
| `params` | 否 | 填进 `?` 的值，一个数组。只能是 `null`、数字、字符串和布尔值 |

| 方法 | 用来做什么 | 返回 |
|---|---|---|
| `db.execute` | 不返回行的语句：建表、插入、更新、删除 | `{ "changes": 1, "lastInsertRowid": 1 }` |
| `db.query` | 返回行的语句 | `[{ "date": "2026-10-22", "minutes": 25 }]`，每行一个对象，键是列名 |

限制，不合就报错：

- 一次只能有一条语句。
- 每条最多运行 5 秒。
- SQL 本身最长 100,000 字节。一个值或一行最大 256,000 字节。
- `db.query` 的结果最大 10 MB，多了用 `LIMIT` 分几次读。结果里不能有 BLOB。
- 数据库不能比 `storage_mb` 大。
- 不能用 `ATTACH`、临时表和 `load_extension`。
- PRAGMA 只能用 `user_version`、`table_info`、`table_xinfo`、`index_list`、`index_info`、`foreign_key_list`。
- 虚表只能建 `fts5` 和 `rtree`。
- 不能用 `json_group_array`、`json_group_object` 和它们的 `jsonb_` 版本。

- 每次调用都重新打开数据库，调完就关。所以几条语句不能放进同一个事务：分开调 `BEGIN` 和 `COMMIT` 没有用。要一次改好几行，写成一条语句，比如 `INSERT … SELECT`，或者带 `ON CONFLICT` 的 `INSERT`。
- 所有插件同时最多打开 4 个数据库，多的排队等。

### island.show、island.hide

见 [岛](island.md)。

## 事件

只有后台脚本收得到。

```js
hindsight.on("focus.changed", (event) => {
  // …
});
```

### focus.changed

要 `focus.changed` 权限，`runs_in_background` 也要是 `true`。用户切到别的应用、别的网站，或者离开电脑时发。

```json
{
  "at": "2026-10-22T10:30:00+09:00",
  "away": false,
  "app": "Google Chrome",
  "category": { "id": "code", "name": "Coding", "color": "#a78bfa", "icon": "Code", "superCategory": null },
  "title": "Pull requests",
  "host": "github.com"
}
```

| 字段 | 说明 | 要的权限 |
|---|---|---|
| `at` | 焦点换到这里、或者用户离开的时刻。RFC 3339，可能带小数秒，`Date.parse()` 读得了 | 不要 |
| `away` | `true` 是用户离开了电脑 | 不要 |
| `app` | 应用名 | `focus.app` |
| `category` | 分类，格式和 `categories.list` 的一项一样 | `focus.category` |
| `title` | 窗口标题 | `focus.title` |
| `host` | 网站的域名，不是完整的网址 | `focus.title` |

- 没有权限的字段是 `null`。
- `away` 是 `true` 时，别的字段都是 `null`。
- 统计里不显示的窗口，比如隐藏的应用、被忽略规则排除的窗口，也会发事件：只有 `at`，`away` 是 `false`，别的字段是 `null`。这样插件知道焦点离开了上一个窗口。
- 窗口标题匹配用户的隐私关键词时，`title` 是 `null`。
- 事件的时间不会倒退。
- 后台脚本启动之前的事件收不到。

### window.changed

不要权限。插件自己的窗口打开、最小化、还原、关掉时发。

```json
{ "state": "minimized" }
```

- `state` 是 `"open"`、`"minimized"` 或 `"closed"`。从最小化还原时是 `"open"`。
- 只在页面开在单独的窗口里时发。开在主窗口里不发。
- 后台脚本启动时不补发。这时插件的窗口还没打开。

### island.clicked

不要权限。插件放在岛上的按钮被点时发，见 [button](island/button.md)。

```json
{ "button": "pause" }
```
