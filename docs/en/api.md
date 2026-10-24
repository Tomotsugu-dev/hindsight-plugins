# API reference

Plugins require Hindsight 0.10.0 or later. Everything on this page is available from 0.10.0 unless a later version is specified.

## manifest.json

```json
{
  "id": "welcome-back",
  "name": "Welcome back",
  "version": "0.1.0",
  "permissions": ["focus.changed", "notifications", "stats.read", "stats.today"],
  "runs_in_background": true,
  "storage_mb": 1,
  "opens_in": "window",
  "window": { "width": 360, "height": 480 }
}
```

| Field | Required? | Description |
|---|---|---|
| `id` | Yes | Lowercase letters, digits, and `-`; cannot start or end with `-`; at most 63 characters. Must be unique in the plugin market |
| `name` | Yes | Nonempty name shown to the user. Also used as the notification title |
| `version` | Yes | Three numbers, such as `0.1.0`. `v0.1.0` and `0.1.0-beta` are invalid |
| `permissions` | Yes | Requested permissions; see [Permissions](permissions.md). Use `[]` if none are needed |
| `runs_in_background` | Yes | When `true`, Hindsight runs `background.js` for as long as Hindsight is running |
| `storage_mb` | No | Maximum size of the plugin's database in MB, from 1 to 10240. Without it, `db.execute` and `db.query` are unavailable |
| `opens_in` | No | Default location for the page: `"main"` in the main window's sidebar, or `"window"` in a separate window. If omitted, the page does not appear in the sidebar; the user opens it from Settings in a separate window. The user can change this in Settings |
| `window` | No | Initial size when the page first opens in a separate window. Each dimension is at least 200, with a maximum of 2560×1440. Defaults to 900×640 |

- Unknown fields are ignored.
- During installation, the user sees and accepts `permissions` and `storage_mb`; see [What the user sees during installation](permissions.md#what-the-user-sees-during-installation).

## Package

| File | Description |
|---|---|
| `manifest.json` | Required; at most 64 KB |
| `background.js` | Required if `runs_in_background` is `true` |
| `ui/index.html` | Required to provide a page |
| `icon.png` | Optional; otherwise the default icon is used. PNG, at most 256 KB |

- Put these files at the top level of the zip archive.
- The zip may contain at most 1,000 files and must expand to at most 100 MB.
- `background.js` runs in a Worker as a classic script, not an ES module, so it cannot use `import`. To split it into files, use `importScripts("lib.js")`; paths start at the archive's top level.

## Calling methods and receiving events

| | Background script | Page |
|---|---|---|
| Call methods | `hindsight.call(method, params)` | Load `../_page.js` first, then call `hindsight.call(method, params)` |
| Receive events | `hindsight.on(name, callback)` | Cannot receive events |

`hindsight.call()` returns a Promise. On failure, it rejects with an `Error` whose message explains the cause:

| Cause | Message |
|---|---|
| Plugin disabled | `plugin not enabled: <plugin id>` |
| Unknown method | `plugin unknown method: <method name>` |
| Missing permission | `plugin has no permission: <permission name>` |
| Invalid parameters | `invalid input: …` |

## Methods

See [Permissions](permissions.md) for what each permission allows.

| Method | Required permission | What it does |
|---|---|---|
| `stats.day_by_category` | `stats.read` and one date range | Time spent in each category on a given day |
| `categories.list` | `categories.read` | List all categories |
| `super_categories.list` | `super_categories.read` | List all supercategories |
| `notifications.send` | `notifications`; also `notifications.sound` for sound | Send a system notification |
| `db.execute`, `db.query` | No permission, but requires `storage_mb` | Read or write the plugin's database |
| `island.show`, `island.hide` | `island` | Show or remove content on the island; see [Island](island.md) |

### stats.day_by_category

```js
hindsight.call("stats.day_by_category", { date: "2026-10-22" });
```

| Parameter | Required? | Description |
|---|---|---|
| `date` | Yes | `YYYY-MM-DD` in the computer's local date. Cannot be after today |
| `devices` | No | `"this"` (default) counts only this computer; `"selected"` counts the devices selected in the main window and requires `devices.read` |

Returns the categories used on that day, ordered by time spent, longest first:

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

- `superCategory` is `null` for a category outside a supercategory.
- To get a supercategory's total time, add the `seconds` of its categories yourself.

The available dates depend on the plugin's date range permission:

| Permission | Available dates |
|---|---|
| `stats.today` | Today |
| `stats.week` | This Monday through today |
| `stats.month` | The first day of this month through today, plus this week |
| `stats.history` | All dates |

- A wider range includes narrower ranges.
- If a date is outside the available range, the error names the range needed to read it, such as `plugin has no permission: stats.week`.

### categories.list

```js
hindsight.call("categories.list");
```

Returns all categories in the same order as the main window. Each item has the same fields as one from `stats.day_by_category`, except `seconds`.

`stats.day_by_category` returns only categories used on the requested day. Use this method when a plugin's settings page needs to let the user choose from all categories.

### super_categories.list

```js
hindsight.call("super_categories.list");
```

Returns all supercategories in the same order as the main window:

```json
[{ "id": "work", "name": "Work", "color": "#8b5cf6", "icon": "Briefcase" }]
```

### notifications.send

```js
hindsight.call("notifications.send", { body: "You have watched YouTube for 10 minutes" });
hindsight.call("notifications.send", { body: "This session is over", sound: true });
```

| Parameter | Required? | Description |
|---|---|---|
| `body` | Yes | Nonempty notification text |
| `sound` | No | When `true`, also plays the system alert sound; requires `notifications.sound`. Available from 0.10.1 |

- The title is always the plugin's `name`.
- A notification has no sound unless `sound` is set.
- If `sound` is `true` without `notifications.sound`, the call fails and sends no notification.
- Only the default system alert sound is available.
- There is no rate limit. Users may disable a plugin that sends too many notifications.

### db.execute, db.query

Each plugin has its own SQLite database, inaccessible to other plugins.

- Data is retained when the plugin is updated. On uninstall, the user chooses whether to delete it.
- Data does not sync to the user's other devices.
- Set `storage_mb` in the manifest and have the user accept it during installation. Without it, calls fail with `plugin has no permission: storage_mb`.

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

| Parameter | Required? | Description |
|---|---|---|
| `sql` | Yes | One SQL statement |
| `params` | No | Array of values for `?` placeholders. Values can only be `null`, numbers, strings, or booleans |

| Method | Use | Returns |
|---|---|---|
| `db.execute` | Statements that do not return rows: create table, insert, update, delete | `{ "changes": 1, "lastInsertRowid": 1 }` |
| `db.query` | Statements that return rows | `[{ "date": "2026-10-22", "minutes": 25 }]`, one object per row, keyed by column name |

Calls fail if they exceed these limits:

- Only one statement per call.
- At most 5 seconds per statement.
- SQL text at most 100,000 bytes. A single value or row at most 256,000 bytes.
- A `db.query` result at most 10 MB; use `LIMIT` to read it in batches. Results cannot contain BLOBs.
- The database cannot exceed `storage_mb`.
- `ATTACH`, temporary tables, and `load_extension` are unavailable.
- Only these PRAGMAs are allowed: `user_version`, `table_info`, `table_xinfo`, `index_list`, `index_info`, `foreign_key_list`.
- Only `fts5` and `rtree` virtual tables may be created.
- `json_group_array`, `json_group_object`, and their `jsonb_` variants are unavailable.

Each call opens and closes the database. Separate calls therefore cannot share a transaction: calling `BEGIN` and `COMMIT` separately does not work. To change several rows atomically, use one statement such as `INSERT … SELECT` or `INSERT` with `ON CONFLICT`.

Across all plugins, at most four databases can be open at once; additional calls wait in a queue.

### island.show, island.hide

See [Island](island.md).

## Events

Only the background script receives events.

```js
hindsight.on("focus.changed", (event) => {
  // …
});
```

### focus.changed

Requires `focus.changed` and `runs_in_background: true`. Sent when the user switches apps or websites, or leaves the computer.

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

| Field | Description | Required permission |
|---|---|---|
| `at` | When focus changed to this window or the user left. RFC 3339, possibly with fractional seconds; readable by `Date.parse()` | None |
| `away` | `true` when the user has left the computer | None |
| `app` | Application name | `focus.app` |
| `category` | Category, with the same fields as an item from `categories.list` | `focus.category` |
| `title` | Window title | `focus.title` |
| `host` | Website domain, not the full URL | `focus.title` |

- Fields without permission are `null`.
- When `away` is `true`, all other fields besides `at` are `null`.
- Windows excluded from statistics, such as hidden apps or windows excluded by ignore rules, still cause an event. Only `at` is provided; `away` is `false` and the other fields are `null`. This lets the plugin know focus left the previous window.
- When a window title matches the user's privacy keywords, `title` is `null`.
- Event times never move backward.
- Events from before the background script started are not delivered.

### window.changed

Requires no permission. Sent when the plugin's own window opens, is minimized, is restored, or closes.

```json
{ "state": "minimized" }
```

- `state` is `"open"`, `"minimized"`, or `"closed"`. Restoring a minimized window sends `"open"`.
- Sent only when the page is in a separate window, not in the main window.
- No initial event is sent when the background script starts, since the plugin's window has not opened yet.

### island.clicked

Requires no permission. Sent when a button placed by the plugin on the island is clicked; see [button](island/button.md).

```json
{ "button": "pause" }
```
