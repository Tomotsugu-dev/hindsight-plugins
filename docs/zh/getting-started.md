# 写一个 Hindsight 插件

插件是一个 zip 包，里面是网页代码：HTML 和 JavaScript。Hindsight 装上它以后，在自己的窗口里运行这些代码。插件通过 Hindsight 给的接口读数据、收事件、发通知。

这篇从零写一个插件，装到自己的电脑上。每个方法和事件的细节见 [接口参考](api.md)。插件要 Hindsight 0.10.0 或更新的版本。

## 插件能做什么

- 读每天各分类用了多久
- 在用户切换窗口、离开电脑时收到事件
- 发系统通知
- 在 macOS 菜单栏正中间的岛上显示内容，见 [岛](island.md)
- 用自己的 SQLite 数据库存数据
- 有自己的页面，在主窗口或单独的窗口里打开

存数据之外，每一项都要一个权限。插件在 manifest 里列出要的权限，用户安装时看到这些权限，同意了才能装。全部权限见 [权限](permissions.md)。

## 插件不能做什么

- 不能联网。插件的每个文件都带着同一份 CSP：只能加载包里的文件，发不出任何请求。
- 只能用 [接口参考](api.md) 里列的方法，调不了 Hindsight 的其他功能。
- 读不到截图、AI 报告和聊天记录。窗口标题和网站域名要 `focus.title` 权限才有，完整的网址永远拿不到。
- 不能往岛上放自己的 HTML，只能放 Hindsight 给的几种组件。

## 一个插件的两份代码

| | 后台脚本 `background.js` | 页面 `ui/index.html` |
|---|---|---|
| 什么时候运行 | Hindsight 开着就一直运行，主窗口关了也在 | 用户打开页面时 |
| 在哪里运行 | 一个 Worker 里，没有 DOM | 一个 iframe 里 |
| 调方法 | `hindsight.call()` | `hindsight.call()`，要先加载 `../_page.js` |
| 收事件 | `hindsight.on()` | 收不到 |
| 必须有吗 | manifest 里 `runs_in_background` 是 `true` 时必须有 | 可以没有，没有就没有页面 |

两份代码不共享变量。要共享数据，就都读写插件自己的数据库。

`background.js` 是普通脚本，不是 ES 模块，不能写 `import`。要拆成几个文件，用 `importScripts()` 加载，见 [接口参考](api.md#包)。

## 包里的文件

```
manifest.json    必须有
icon.png         可以没有；PNG，最大 256 KB
background.js    runs_in_background 是 true 时必须有
ui/index.html    可以没有；有它才有页面
```

别的文件随便放，用相对路径引用。打 zip 时这些文件要在最上层，外面不要再套一层文件夹。

## 写一个「欢迎回来」插件

它做两件事：

- 离开电脑再回来时，发一条通知，说离开了几分钟。
- 页面上列出今天各分类用了多久。

新建一个文件夹 `welcome-back`，放下面四个文件。

### manifest.json

```json
{
  "id": "welcome-back",
  "name": "欢迎回来",
  "version": "0.1.0",
  "permissions": ["focus.changed", "notifications", "stats.read", "stats.today"],
  "runs_in_background": true,
  "opens_in": "main"
}
```

- `id`：小写字母、数字和 `-`，最长 63 个字符。插件市场里不能重名。
- `version`：三段数字，比如 `0.1.0`。
- `permissions`：`focus.changed` 收焦点事件，`notifications` 发通知，`stats.read` 加 `stats.today` 读今天的统计。
- `opens_in`：`"main"` 在主窗口的侧栏里打开页面，`"window"` 在单独的窗口里打开。这只是默认值，用户可以在设置里改。

全部字段见 [接口参考](api.md)。

### background.js

```js
// 离开电脑的时刻；没离开时是 null
let awaySince = null;

hindsight.on("focus.changed", (event) => {
  const at = Date.parse(event.at);
  if (event.away) {
    awaySince = at;
    return;
  }
  if (awaySince === null) return;
  const minutes = Math.round((at - awaySince) / 60000);
  awaySince = null;
  hindsight.call("notifications.send", { body: `欢迎回来，你离开了 ${minutes} 分钟` });
});
```

- 用户离开电脑时，Hindsight 发一个 `away` 是 `true` 的 `focus.changed`。用户回来、用到某个窗口时，再发一个 `away` 是 `false` 的。
- 通知的标题固定是插件名。

### ui/index.html

```html
<!doctype html>
<meta charset="utf-8" />
<h1>今天</h1>
<ul id="list"></ul>
<script src="../_page.js"></script>
<script src="page.js"></script>
```

- `../_page.js` 由 Hindsight 提供，不用放进包里，加载后页面里才有 `hindsight.call()`。它的地址在包的最上层，所以从 `ui/` 里引用要加 `../`。
- 脚本要写在单独的 `.js` 文件里：CSP 不允许写在 HTML 里的脚本，也不允许 `onclick=` 这类属性。

### ui/page.js

```js
const now = new Date();
const pad = (n) => String(n).padStart(2, "0");
const date = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;

hindsight
  .call("stats.day_by_category", { date })
  .then((categories) => {
    const list = document.getElementById("list");
    for (const c of categories) {
      const li = document.createElement("li");
      li.textContent = `${c.name}：${Math.round(c.seconds / 60)} 分钟`;
      list.append(li);
    }
  })
  .catch((e) => {
    document.body.append(`出错了：${e.message}`);
  });
```

- `date` 是本机的日期。`stats.today` 只能读今天，读别的日子会报错。
- 默认只算这台电脑的数据。
- 返回的分类按用时从多到少排。

## 装到自己的电脑上

1. 把 `welcome-back` 里的文件打成 zip：
   - macOS：`cd welcome-back && zip -r ../welcome-back-0.1.0.zip .`
   - Windows（PowerShell）：`Compress-Archive -Path welcome-back\* -DestinationPath welcome-back-0.1.0.zip`
2. 在 Hindsight 里打开「设置 → 插件」，在「从文件安装」里点「打开文件夹」，把 zip 放进去，再点「刷新」。
3. 列表里出现这个插件。看一遍它要的权限，点安装。
4. 侧栏里出现「欢迎回来」，点开就是你的页面。

装不上时，列表里写着原因，比如 manifest 哪个字段不对。

改了代码要重新装。同一个版本号不能装第二次，所以先把 `version` 加一，比如改成 `0.1.1`，再打包放进同一个文件夹安装，Hindsight 会把它当成更新。也可以先卸载，再装。

## 调试

- 正式版没有开发者工具，看不到插件的 `console` 输出。
- `hindsight.call()` 失败时，它返回的 Promise 会 reject，`Error` 的 message 写着原因，比如缺哪个权限、参数哪里不对。开发时把它显示在页面上。
- 后台脚本大约 20 秒不回应 Hindsight 的心跳就会被停掉，比如卡在死循环里。停掉以后不会自己重启：在设置里把插件关掉再打开，或者重启 Hindsight。

## 发布

插件市场的列表就在这个仓库里。上架插件或新版本，要给这个仓库提 PR：改 `plugins.json`，加上图标。步骤、字段和审核看什么，见 [CONTRIBUTING.md](../../CONTRIBUTING.md)（英文）。

不上架也行：把 zip 发给别人，对方按「装到自己的电脑上」的步骤安装。

## 接下来

- [接口参考](api.md)：manifest 的全部字段、每个方法和事件、各种上限
- [权限](permissions.md)：每个权限允许做什么、要和谁一起申请、安装时用户看到什么
- [岛](island.md)：在岛上放什么、怎么放
