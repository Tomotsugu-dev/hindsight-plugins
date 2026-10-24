# Permissions

A plugin lists its requested permissions in the manifest's `permissions` field. During installation, the user sees what each permission does and must check a box to accept them.

Plugins require Hindsight 0.10.0 or later. All permissions on this page are available from 0.10.0 unless a later version is specified.

## All permissions

### Read statistics

| Permission | What it allows | Must be requested with |
|---|---|---|
| `stats.read` | Use [`stats.day_by_category`](api.md#statsday_by_category) to read time spent in each category on each day. Does not include window titles or URLs | At least one date range |
| `stats.today` | Read today | `stats.read` |
| `stats.week` | Read this Monday through today | `stats.read` |
| `stats.month` | Read the first day of this month through today, plus this week | `stats.read` |
| `stats.history` | Read all dates | `stats.read` |
| `devices.read` | Count devices selected in the main window with `stats.day_by_category`. Without it, only this computer is counted | |
| `categories.read` | List all categories with [`categories.list`](api.md#categorieslist) | |
| `super_categories.read` | List all supercategories with [`super_categories.list`](api.md#super_categorieslist) | |

- Each wider date range includes the narrower ones.
- A manifest with `stats.read` but no date range fails validation. This ensures the user can see how far back the plugin can read during installation.

### Receive focus events

| Permission | What it allows | Must be requested with |
|---|---|---|
| `focus.changed` | Receive [`focus.changed`](api.md#focuschanged) events, containing only `at` and `away` | `runs_in_background: true` in the manifest |
| `focus.app` | Add the application name to the event | `focus.changed` |
| `focus.category` | Add the category to the event | `focus.changed` |
| `focus.title` | Add the window title and website domain to the event | `focus.changed` |

### System features

| Permission | What it allows | Must be requested with |
|---|---|---|
| `notifications` | Send system notifications with [`notifications.send`](api.md#notificationssend) | |
| `notifications.sound` | Play the system alert sound with a notification. Available from 0.10.1 | `notifications` |
| `island` | Put content on and remove it from the island with `island.show` and `island.hide`; see [Island](island.md) | |

## Features without a permission

- Reading and writing the plugin's own database. The manifest must still include `storage_mb`; otherwise the call fails with `plugin has no permission: storage_mb`. See [`db.execute`, `db.query`](api.md#dbexecute-dbquery).
- `window.changed` events: only this plugin receives events about its own window.
- `island.clicked` events: only a plugin that placed a button on the island can receive them, and placing a button already requires `island`.

## Validation

A manifest that fails validation cannot be installed:

| Cause | Error |
|---|---|
| This version of Hindsight does not recognize the permission | `plugin unknown permission: <permission name>` |
| A required companion permission is missing | `plugin manifest: <permission name> needs <required permission>` |
| `stats.read` has no date range | `plugin manifest: stats.read needs one of stats.today, stats.week, stats.month, stats.history` |
| `focus.changed` is present but `runs_in_background` is not `true` | `plugin manifest: focus.changed needs runs_in_background` |

- A plugin requesting a permission introduced in a later version cannot be installed on an older Hindsight. For example, a plugin requesting `notifications.sound` cannot be installed on 0.10.0; the user must update Hindsight first.
- If a method call lacks permission, the Promise returned by `hindsight.call()` rejects with `plugin has no permission: <permission name>`.

## What the user sees during installation

- One line explaining each requested permission. `focus.title` is marked “high risk.”
- If `storage_mb` is set, the maximum disk space in MB.
- When installing from a file with `runs_in_background: true`, a line describing background execution. This line is not shown for installation from the plugin market.
- A checkbox that the user must select before installing.
- For an unofficial plugin, a warning that it may cause personal information to leak. All plugins installed from a file are treated as unofficial.

For a plugin that requests nothing, the dialog says that the plugin does not read any of the user's data.

## Capabilities no permission can grant

- Network access. See [What a plugin cannot do](getting-started.md#what-a-plugin-cannot-do).
- Screenshots, AI daily reports, and AI chat history.
- Full URLs. `focus.title` provides only the domain.
