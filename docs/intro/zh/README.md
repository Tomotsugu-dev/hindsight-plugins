<p align="center">
  <img src="../../images/hindsight-logo.png" alt="Hindsight" width="140">
</p>

<h1 align="center">Hindsight 插件、主题市场</h1>

<p align="center">
  查找插件和主题，编写自己的插件，并提交上架。
</p>

<p align="center">
  <a href="README.md">简体中文</a> · <a href="../zh-TW/README.md">繁體中文</a> · <a href="../../../README.md">English</a> · <a href="../ja/README.md">日本語</a> · <a href="../pt/README.md">Português</a> · <a href="../es/README.md">Español</a>
</p>

<p align="center">
  <a href="https://github.com/Tomotsugu-dev/Hindsight/releases"><img alt="Hindsight 最新版本" src="https://img.shields.io/github/v/release/Tomotsugu-dev/Hindsight?color=blue&amp;logo=github"></a>
  <a href="../../../LICENSE"><img alt="MIT 许可证" src="https://img.shields.io/badge/license-MIT-green"></a>
</p>

<p align="center">
  <a href="#插件">浏览插件</a> · <a href="#写插件">编写插件</a> · <a href="#上架插件">上架插件</a> · <a href="#主题">主题</a>
</p>

---

[Hindsight](https://github.com/Tomotsugu-dev/Hindsight) 插件市场的插件列表。用户每次打开「设置 → 插件」时，Hindsight 从这个仓库的 `main` 分支读取 [plugins.json](../../../plugins.json) 和 [icons/](../../../icons/) 里的图标。

这个仓库也放着[主题网站](https://hindsight.kyosweb.com/themes/)的主题列表 [themes.json](../../../themes.json)。

## 插件

| 图标 | 插件 | 做什么 | 源码 |
|---|---|---|---|
| <img src="../../../icons/hindsight-focus.png" alt="" width="28"> | Focus | 按工作节奏计时，摸鱼时提醒，支持灵动岛 | [Tomotsugu-dev/hindsight-focus](https://github.com/Tomotsugu-dev/hindsight-focus) |

## 写插件

开发文档另有[英文版](../../en/getting-started.md)。

- [写一个 Hindsight 插件](../../zh/getting-started.md)：从零写一个小插件，用 zip 装到自己的电脑上
- [接口参考](../../zh/api.md)：manifest 的字段、方法、事件和各种上限
- [权限](../../zh/permissions.md)：每个权限允许做什么、要和谁一起申请、安装时用户看到什么
- [岛](../../zh/island.md)：插件能在 macOS 菜单栏的岛上显示什么，每个组件一页

插件要 Hindsight 0.10.0 或更新的版本。

## 上架插件

插件和新版本都通过 pull request 上架。步骤、`plugins.json` 的字段和审核看什么，见 [CONTRIBUTING.md](../../../CONTRIBUTING.md)（英文）。

## 主题

主题改变 Hindsight 的样子。[主题网站](https://hindsight.kyosweb.com/themes/)上的每个主题都能先在网页里试用，再下载。下载后解压，在 Hindsight 的「设置 → 外观 → 自定义主题」里点「导入主题」，选 `theme.json`。

- 主题文件怎么写：[写一个 Hindsight 主题](../../zh/themes.md)
- 怎么上架主题：CONTRIBUTING.md 的 [Themes](../../../CONTRIBUTING.md#themes)（英文）

主题要 Hindsight 0.10.2 或更新的版本。

## 第三方插件

谁都可以通过 pull request 提交插件。每个插件都经过审核才上架。仓库不在 `Tomotsugu-dev` 下的插件是第三方插件：安装前，用户会看到提醒，说它不是官方插件，有可能造成个人信息泄漏。

<h2 align="center">许可证</h2>

<p align="center">
  这个仓库里的插件列表以 <a href="../../../LICENSE">MIT 许可证</a>发布。<br/>
  每个插件遵循它自己仓库的许可证。
</p>
