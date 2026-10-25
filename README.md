<p align="center">
  <img src="docs/images/hindsight-logo.png" alt="Hindsight" width="140">
</p>

<h1 align="center">Hindsight Plugin and Theme Market</h1>

<p align="center">
  Browse plugins and themes, build your own plugin, and submit it to the market.
</p>

<p align="center">
  <a href="docs/intro/zh/README.md">简体中文</a> · <a href="docs/intro/zh-TW/README.md">繁體中文</a> · <a href="README.md">English</a> · <a href="docs/intro/ja/README.md">日本語</a> · <a href="docs/intro/pt/README.md">Português</a> · <a href="docs/intro/es/README.md">Español</a>
</p>

<p align="center">
  <a href="https://github.com/Tomotsugu-dev/Hindsight/releases"><img alt="Latest Hindsight release" src="https://img.shields.io/github/v/release/Tomotsugu-dev/Hindsight?color=blue&amp;logo=github"></a>
  <a href="LICENSE"><img alt="MIT License" src="https://img.shields.io/badge/license-MIT-green"></a>
</p>

<p align="center">
  <a href="#plugins">Browse plugins</a> · <a href="#writing-a-plugin">Build a plugin</a> · <a href="#submit-a-plugin">Submit a plugin</a> · <a href="#themes">Themes</a>
</p>

---

The plugin list for the plugin market in [Hindsight](https://github.com/Tomotsugu-dev/Hindsight). Each time the user opens Settings → Plugins, Hindsight reads [plugins.json](plugins.json) and the icons in [icons/](icons/) from the `main` branch of this repository.

This repository also holds [themes.json](themes.json), the theme list of the [theme website](https://hindsight.kyosweb.com/themes/).

## Plugins

| Icon | Plugin | What it does | Source |
|---|---|---|---|
| <img src="icons/hindsight-focus.png" alt="" width="28"> | Focus | Times your work to a rhythm, notifies you when you get distracted, and works with the island | [Tomotsugu-dev/hindsight-focus](https://github.com/Tomotsugu-dev/hindsight-focus) |

## Writing a plugin

The developer docs are available in [English](docs/en/getting-started.md) and [简体中文](docs/zh/getting-started.md):

- [Getting started](docs/en/getting-started.md): write a small plugin and install it from a zip
- [API reference](docs/en/api.md): manifest fields, methods, events and limits
- [Permissions](docs/en/permissions.md): what each permission allows, what it must be requested with, and what the user sees at install
- [The island](docs/en/island.md): what a plugin can show on the island in the macOS menu bar, with a page for each component

Plugins need Hindsight 0.10.0 or later.

## Submit a plugin

Plugins and new versions are listed by pull request. See [CONTRIBUTING.md](CONTRIBUTING.md) for the steps, the fields of `plugins.json`, and what review checks.

## Themes

A theme changes how Hindsight looks. On the [theme website](https://hindsight.kyosweb.com/themes/), you can try each theme in your browser before you download it. Unzip the download, then in Hindsight open Settings → Appearance → Custom themes, click Import theme, and choose `theme.json`.

- Make a theme: [Write a Hindsight theme](docs/en/themes.md), also in [简体中文](docs/zh/themes.md)
- List a theme: [Themes](CONTRIBUTING.md#themes) in CONTRIBUTING.md

Themes need Hindsight 0.10.2 or later.

## Third-party plugins

Anyone can submit a plugin by pull request. Every plugin is reviewed before it is listed. A plugin whose repository is not under `Tomotsugu-dev` is a third-party plugin: before installing it, the user is warned that it is not official and could leak personal information.

<h2 align="center">License</h2>

<p align="center">
  The plugin list in this repository is released under the <a href="LICENSE">MIT License</a>.<br/>
  Each plugin is distributed under the license of its own repository.
</p>
