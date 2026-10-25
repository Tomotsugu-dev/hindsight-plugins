# Contributing

This repository holds the list behind the Hindsight plugin market: [plugins.json](plugins.json) and the icons in [icons/](icons/). It also holds [themes.json](themes.json), the list behind the [theme website](https://hindsight.kyosweb.com/themes/). It holds no plugin or theme code. To list a plugin, a theme or a new version, open a pull request that changes these files.

Anyone can submit a plugin. A plugin whose repository is not under `Tomotsugu-dev` is a third-party plugin: before installing it, the user is warned that it is not official and could leak personal information.

## Before you open a pull request

- The plugin installs from a zip and works. See [Install it on your computer](docs/en/getting-started.md#install-it-on-your-computer).
- Its code is in a public GitHub repository.
- The zip is a release asset in that repository, such as `https://github.com/someone/hindsight-pomodoro/releases/download/0.1.0/hindsight-pomodoro-0.1.0.zip`.

Do not replace a zip that is already listed. Its SHA-256 would change, and every download would fail. Publish a new version instead.

## Listing a new plugin

1. Fork this repository and create a branch.
2. Add your plugin to `plugins` in `plugins.json`:

   ```json
   {
     "id": "hindsight-pomodoro",
     "name": "Pomodoro",
     "author": "someone",
     "description": {
       "zh-CN": "25 分钟专注，5 分钟休息",
       "en": "Focus for 25 minutes, then rest for 5"
     },
     "repo": "someone/hindsight-pomodoro",
     "versions": [
       {
         "version": "0.1.0",
         "url": "https://github.com/someone/hindsight-pomodoro/releases/download/0.1.0/hindsight-pomodoro-0.1.0.zip",
         "sha256": "…",
         "permissions": ["notifications", "island"],
         "storage_mb": 1
       }
     ]
   }
   ```

3. Add `icons/<id>.png`: the same file as `icon.png` in your zip.
4. Check that the file is still valid JSON: `python3 -m json.tool plugins.json > /dev/null`
5. Open a pull request titled `feat: list <name>`, such as `feat: list Pomodoro`.

## Listing a new version

1. Publish the zip as a release asset.
2. Add the version to the start of `versions`, with its own `url`, `sha256`, `permissions` and `storage_mb`.
3. If the icon changed, replace `icons/<id>.png`.
4. Open a pull request titled `feat: list <name> <version>`, such as `feat: list Pomodoro 0.2.0`.

Older versions can stay in `versions`. The market offers the newest one, whatever the order in the file, and users can pick an older one from the menu of an installed plugin.

## plugins.json

`format_version` is 2. Hindsight 0.10.2 and later read only format 2, and 0.10.0 and 0.10.1 only format 1. A version of Hindsight that cannot read the format shows an error in place of the downloadable plugins.

Each plugin:

| Field | Description |
|---|---|
| `id` | Same as `id` in the manifest. No other plugin in the list may use it |
| `name` | Shown in the market. Use the `name` in the manifest: after install, Hindsight shows that one |
| `author` | Your name or GitHub account. Shown in the market, and in the install dialog of a third-party plugin |
| `description` | The description in each language, from an interface language code to the text: `zh-CN`, `zh-TW`, `en`, `ja`, `pt-BR` or `es`. The market shows the interface language; without it, `en`; without `en`, the first language by code. Codes must match exactly: `zh-TW` does not fall back to `zh-CN`. Include at least `en` |
| `repo` | Your plugin's repository, as `owner/name`. A plugin whose repository is under `Tomotsugu-dev` is official: its install dialog has no warning about third-party plugins |
| `versions` | The versions users can install |

Each version:

| Field | Description |
|---|---|
| `version` | Same as `version` in the manifest, such as `0.1.0`. A version that is not three numbers is skipped |
| `url` | The zip, a release asset of `repo`. At most 500 MB |
| `sha256` | SHA-256 of the zip |
| `permissions` | Copy from the manifest |
| `storage_mb` | Copy from the manifest. Leave it out if the manifest has none |

- The user agrees to `permissions` and `storage_mb` as written here, and the plugin gets exactly these. Hindsight does not compare them with the manifest, so a permission missing here makes the plugin's calls fail.
- After the download, Hindsight checks the SHA-256 and the `id` and `version` in the zip's manifest. If any of them does not match, the zip is deleted.
- The market shows `icons/<id>.png` as the plugin's icon, or the default icon if there is none. After install, Hindsight shows `icon.png` from the zip instead.

To get the SHA-256 of a zip:

- macOS: `shasum -a 256 hindsight-pomodoro-0.1.0.zip`
- Windows (PowerShell): `(Get-FileHash hindsight-pomodoro-0.1.0.zip -Algorithm SHA256).Hash`

Upper or lower case both work.

## Review

A script checks each pull request that changes the list, and writes what it found as a comment on the pull request. It checks the rules on this page, and downloads each new zip to check it with the same rules as Hindsight: the SHA-256, the manifest, the permissions and the icon. Fix every problem in the comment.

To run the same check before you open the pull request, commit your changes, then run this with Python 3.9 or later:

```sh
git fetch https://github.com/Tomotsugu-dev/hindsight-plugins.git main
python3 scripts/check_listing.py FETCH_HEAD HEAD
```

Then the maintainer checks that:

- `repo` is yours and holds the plugin's code;
- the plugin installs and works.

After the merge, the plugin shows up the next time users open Settings → Plugins. GitHub caches the list for up to 5 minutes, so it can take that long.

## Themes

The [theme website](https://hindsight.kyosweb.com/themes/) lists the themes in `themes.json`. Each theme has three buttons: Preview tries the theme in a demo of Hindsight, Homepage opens your page, and Download opens the release of the newest listed version. To make a theme, see [Write a Hindsight theme](docs/en/themes.md).

### Before you open a pull request

- The theme imports into Hindsight and looks right: Settings → Appearance → Custom themes → Import theme.
- The zip is a release asset in a public GitHub repository.
- The zip holds one folder named after the theme's `id`, with `theme.json` and, if you have one, `theme.css`. The zip is at most 5 MB:

  ```
  harbor-1.0.0.zip
  └── harbor/
      ├── theme.json
      └── theme.css
  ```

Do not replace a zip that is already listed. Its SHA-256 would change, and the website would stop showing the theme. Publish a new version instead.

### Listing a new theme

1. Fork this repository and create a branch.
2. Add your theme to `themes` in `themes.json`:

   ```json
   {
     "id": "harbor",
     "repo": "someone/hindsight-harbor",
     "homepage": "https://someone.github.io/harbor/",
     "versions": [
       {
         "version": "1.0.0",
         "url": "https://github.com/someone/hindsight-harbor/releases/download/1.0.0/harbor-1.0.0.zip",
         "sha256": "…"
       }
     ]
   }
   ```

3. Check that the file is still valid JSON: `python3 -m json.tool themes.json > /dev/null`
4. Open a pull request titled `feat: list the <name> theme`, such as `feat: list the Harbor theme`.

### Listing a new theme version

1. Publish the zip as a release asset.
2. Add the version to the start of `versions`, with its own `url` and `sha256`.
3. Open a pull request titled `feat: list the <name> theme <version>`, such as `feat: list the Harbor theme 1.1.0`.

The website shows only the first version. Keep the older versions: their downloads count toward the theme's total.

### themes.json

`format_version` is 1.

Each theme:

| Field | Description |
|---|---|
| `id` | Same as `id` in `theme.json`. No other theme in the list may use it, and it cannot be `index` |
| `repo` | Your theme's repository, as `owner/name` |
| `homepage` | Optional. Your own page for the theme. It must start with `https://`. Without it, the Homepage button opens `https://github.com/<repo>` |
| `versions` | The listed versions, newest first |

Each version:

| Field | Description |
|---|---|
| `version` | Same as `version` in `theme.json` |
| `url` | The zip, a release asset of `repo` |
| `sha256` | SHA-256 of the zip. Get it the same way as for a [plugin zip](#pluginsjson) |

The name, author and description come from `theme.json` in the zip, so write them only there.

### Theme review

The same script as for plugins checks themes, see [Review](#review). It also checks that `theme.css` loads no files: no `@import`, and `url()` only with `data:` addresses.

Then the maintainer checks that:

- `repo` is yours;
- the theme imports into Hindsight and looks right.

After the merge, the theme shows up on the website within 10 minutes. The website checks the zip again every day. If the zip in the release was replaced, the website stops showing the theme.
