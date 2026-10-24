# Write a Hindsight plugin

A plugin is a zip archive containing web code: HTML and JavaScript. Once installed, Hindsight runs that code in its own window. Plugins use the API provided by Hindsight to read data, receive events, and send notifications.

This guide builds a small plugin from scratch and installs it on your computer. For details of every method and event, see the [API reference](api.md). Plugins require Hindsight 0.10.0 or later.

## What a plugin can do

- Read how much time was spent in each category on a given day
- Receive events when the user switches windows or leaves the computer
- Send system notifications
- Show content on the island in the center of the macOS menu bar; see [Island](island.md)
- Store data in its own SQLite database
- Provide a page that opens in the main window or a separate window

Except for storing its own data, each capability requires a permission. The plugin lists its requested permissions in the manifest. The user sees and accepts them during installation. See [Permissions](permissions.md) for the complete list.

## What a plugin cannot do

- Access the network. Every file in the plugin has the same Content Security Policy (CSP): it can load only files in the archive and cannot make network requests.
- Call Hindsight functions outside those listed in the [API reference](api.md).
- Read screenshots, AI daily reports, or AI chat history. Window titles and website domains require the `focus.title` permission; full URLs are never available.
- Put its own HTML on the island. It can use only the components provided by Hindsight.

## A plugin's two scripts

| | Background script `background.js` | Page `ui/index.html` |
|---|---|---|
| When it runs | As long as Hindsight is running, even if its main window is closed | When the user opens the page |
| Where it runs | In a Worker, without a DOM | In an iframe |
| Calling methods | `hindsight.call()` | `hindsight.call()` after loading `../_page.js` |
| Receiving events | `hindsight.on()` | Cannot receive events |
| Required? | Yes if `runs_in_background` is `true` in the manifest | Optional; without it, the plugin has no page |

The two scripts do not share variables. To share data, both can read and write the plugin's database.

`background.js` is a classic script, not an ES module, so it cannot use `import`. To split it into files, use `importScripts()`; see the [API reference](api.md#package).

## Files in the archive

```
manifest.json    Required
icon.png         Optional; PNG, at most 256 KB
background.js    Required if runs_in_background is true
ui/index.html    Optional; the plugin has a page only if this exists
```

You may include other files and refer to them by relative paths. These files must be at the top level of the zip archive, without an enclosing folder.

## Build a “Welcome back” plugin

It does two things:

- When you return to the computer, it sends a notification saying how many minutes you were away.
- Its page lists how much time you spent in each category today.

Create a folder named `welcome-back` with the following four files.

### manifest.json

```json
{
  "id": "welcome-back",
  "name": "Welcome back",
  "version": "0.1.0",
  "permissions": ["focus.changed", "notifications", "stats.read", "stats.today"],
  "runs_in_background": true,
  "opens_in": "main"
}
```

- `id`: lowercase letters, digits, and `-`, up to 63 characters. It must be unique in the plugin market.
- `version`: three numbers, such as `0.1.0`.
- `permissions`: `focus.changed` receives focus events; `notifications` sends notifications; `stats.read` together with `stats.today` reads today's statistics.
- `opens_in`: `"main"` opens the page in the main window's sidebar; `"window"` opens it in a separate window. This is only the default; the user can change it in Settings.

See the [API reference](api.md) for all fields.

### background.js

```js
// When the user left; null while they are at the computer.
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
  hindsight.call("notifications.send", { body: `Welcome back! You were away for ${minutes} minutes.` });
});
```

- When the user leaves the computer, Hindsight sends a `focus.changed` event with `away: true`. When the user returns and focuses a window, it sends one with `away: false`.
- The notification title is always the plugin's name.

### ui/index.html

```html
<!doctype html>
<meta charset="utf-8" />
<h1>Today</h1>
<ul id="list"></ul>
<script src="../_page.js"></script>
<script src="page.js"></script>
```

- Hindsight provides `../_page.js`; do not include it in the archive. It makes `hindsight.call()` available on the page. The file is at the archive's top level, so a page in `ui/` refers to it with `../`.
- Put scripts in separate `.js` files. The CSP does not allow inline scripts or attributes such as `onclick=`.

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
      li.textContent = `${c.name}: ${Math.round(c.seconds / 60)} minutes`;
      list.append(li);
    }
  })
  .catch((e) => {
    document.body.append(`Error: ${e.message}`);
  });
```

- `date` is the computer's local date. `stats.today` allows only today; another date produces an error.
- By default, only data from this computer is counted.
- The returned categories are ordered from most time spent to least.

## Install it on your computer

1. Make a zip archive of the files in `welcome-back`:
   - macOS: `cd welcome-back && zip -r ../welcome-back-0.1.0.zip .`
   - Windows (PowerShell): `Compress-Archive -Path welcome-back\* -DestinationPath welcome-back-0.1.0.zip`
2. In Hindsight, open Settings → Plugins. Under “Install from file,” click “Open folder,” put the zip there, and click “Refresh.”
3. The plugin appears in the list. Review the permissions it requests and click Install.
4. “Welcome back” appears in the sidebar. Click it to open the page.

If installation fails, the list shows the reason, such as an invalid manifest field.

After changing the code, install it again. The same version cannot be installed twice, so increment `version`, for example to `0.1.1`, then make a new zip and install it from the same folder. Hindsight treats it as an update. You can also uninstall the plugin first.

## Debugging

- The release build has no developer tools, so you cannot see a plugin's `console` output.
- If `hindsight.call()` fails, its Promise rejects with an `Error` whose message explains the cause, such as a missing permission or invalid parameter. Show that message on the page while developing.
- If the background script does not respond to Hindsight's heartbeat for about 20 seconds, for example because it is stuck in an infinite loop, Hindsight stops it. It will not restart automatically. Disable and re-enable the plugin in Settings, or restart Hindsight.

## Publishing

The plugin market's list lives in this repository. To list a plugin or a new version, open a pull request that changes `plugins.json` and adds the icon. See [CONTRIBUTING.md](../../CONTRIBUTING.md) for the steps, fields, and review criteria.

Listing is optional. You can also send the zip to someone else, who can follow the [installation steps](#install-it-on-your-computer).

## Next steps

- [API reference](api.md): all manifest fields, methods, events, and limits
- [Permissions](permissions.md): what each permission allows, what it must be requested with, and what the user sees at installation
- [Island](island.md): what to show there and how
