<p align="center">
  <img src="../../images/hindsight-logo.png" alt="Hindsight" width="140">
</p>

<h1 align="center">Hindsight 外掛、主題市集</h1>

<p align="center">
  瀏覽外掛和主題，撰寫自己的外掛，並提交上架。
</p>

<p align="center">
  <a href="../zh/README.md">简体中文</a> · <a href="README.md">繁體中文</a> · <a href="../../../README.md">English</a> · <a href="../ja/README.md">日本語</a> · <a href="../pt/README.md">Português</a> · <a href="../es/README.md">Español</a>
</p>

<p align="center">
  <a href="https://github.com/Tomotsugu-dev/Hindsight/releases"><img alt="Hindsight 最新版本" src="https://img.shields.io/github/v/release/Tomotsugu-dev/Hindsight?color=blue&amp;logo=github"></a>
  <a href="../../../LICENSE"><img alt="MIT 授權條款" src="https://img.shields.io/badge/license-MIT-green"></a>
</p>

<p align="center">
  <a href="#外掛">瀏覽外掛</a> · <a href="#撰寫外掛">撰寫外掛</a> · <a href="#上架外掛">上架外掛</a> · <a href="#主題">主題</a>
</p>

---

[Hindsight](https://github.com/Tomotsugu-dev/Hindsight) 外掛市集的外掛清單。使用者每次開啟「設定 → 外掛」時，Hindsight 會從這個儲存庫的 `main` 分支讀取 [plugins.json](../../../plugins.json) 和 [icons/](../../../icons/) 裡的圖示。

這個儲存庫也放著[主題網站](https://hindsight.kyosweb.com/themes/)的主題清單 [themes.json](../../../themes.json)。

## 外掛

| 圖示 | 外掛 | 用途 | 原始碼 |
|---|---|---|---|
| <img src="../../../icons/hindsight-focus.png" alt="" width="28"> | Focus | 按工作節奏計時，摸魚時提醒，支援靈動島 | [Tomotsugu-dev/hindsight-focus](https://github.com/Tomotsugu-dev/hindsight-focus) |

## 撰寫外掛

開發文件有[簡體中文](../../zh/getting-started.md)和[英文](../../en/getting-started.md)版本：

- [寫一個 Hindsight 外掛](../../zh/getting-started.md)：從零寫一個小外掛，用 zip 安裝到自己的電腦上
- [API 參考](../../zh/api.md)：manifest 的欄位、方法、事件和各種上限
- [權限](../../zh/permissions.md)：每個權限允許做什麼、要和哪個權限一起申請、安裝時使用者看到什麼
- [島](../../zh/island.md)：外掛能在 macOS 選單列的島上顯示什麼，每個元件一頁

外掛需要 Hindsight 0.10.0 或更新的版本。

## 上架外掛

外掛和新版本都透過 pull request 上架。步驟、`plugins.json` 的欄位和審核項目，請見 [CONTRIBUTING.md](../../../CONTRIBUTING.md)（英文）。

## 主題

主題改變 Hindsight 的外觀。[主題網站](https://hindsight.kyosweb.com/themes/)上的每個主題都能先在網頁裡試用，再下載。下載後解壓縮，在 Hindsight 的「設定 → 外觀 → 自訂主題」裡點「匯入主題」，選 `theme.json`。

- 主題檔案怎麼寫：[寫一個 Hindsight 主題](../../zh/themes.md)（簡體中文）
- 怎麼上架主題：CONTRIBUTING.md 的 [Themes](../../../CONTRIBUTING.md#themes)（英文）

主題需要 Hindsight 0.10.2 或更新的版本。

## 第三方外掛

任何人都可以透過 pull request 提交外掛。每個外掛都經過審核才會上架。儲存庫不在 `Tomotsugu-dev` 底下的外掛是第三方外掛：安裝前，使用者會看到提醒，說明它不是官方外掛，可能造成個人資訊外洩。

<h2 align="center">授權條款</h2>

<p align="center">
  這個儲存庫中的外掛清單以 <a href="../../../LICENSE">MIT 授權條款</a>釋出。<br/>
  每個外掛依其所在儲存庫的授權條款散布。
</p>
