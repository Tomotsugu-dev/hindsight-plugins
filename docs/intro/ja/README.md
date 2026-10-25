<p align="center">
  <img src="../../images/hindsight-logo.png" alt="Hindsight" width="140">
</p>

<h1 align="center">Hindsight プラグイン・テーママーケット</h1>

<p align="center">
  プラグインとテーマを探し、自分のプラグインを作り、マーケットに掲載できます。
</p>

<p align="center">
  <a href="../zh/README.md">简体中文</a> · <a href="../zh-TW/README.md">繁體中文</a> · <a href="../../../README.md">English</a> · <a href="README.md">日本語</a> · <a href="../pt/README.md">Português</a> · <a href="../es/README.md">Español</a>
</p>

<p align="center">
  <a href="https://github.com/Tomotsugu-dev/Hindsight/releases"><img alt="Hindsight の最新リリース" src="https://img.shields.io/github/v/release/Tomotsugu-dev/Hindsight?color=blue&amp;logo=github"></a>
  <a href="../../../LICENSE"><img alt="MIT ライセンス" src="https://img.shields.io/badge/license-MIT-green"></a>
</p>

<p align="center">
  <a href="#プラグイン">プラグインを見る</a> · <a href="#プラグインを作る">プラグインを作る</a> · <a href="#プラグインを掲載する">掲載する</a> · <a href="#テーマ">テーマ</a>
</p>

---

[Hindsight](https://github.com/Tomotsugu-dev/Hindsight) のプラグインマーケットに載るプラグインの一覧です。ユーザーが「設定 → プラグイン」を開くたびに、Hindsight はこのリポジトリの `main` ブランチから [plugins.json](../../../plugins.json) と [icons/](../../../icons/) のアイコンを読み込みます。

このリポジトリには、[テーマサイト](https://hindsight.kyosweb.com/themes/)のテーマ一覧 [themes.json](../../../themes.json) もあります。

## プラグイン

| アイコン | プラグイン | できること | ソース |
|---|---|---|---|
| <img src="../../../icons/hindsight-focus.png" alt="" width="28"> | Focus | 作業のリズムに合わせて時間を計り、サボっているときに知らせます。アイランドに対応 | [Tomotsugu-dev/hindsight-focus](https://github.com/Tomotsugu-dev/hindsight-focus) |

## プラグインを作る

開発者向けドキュメントは[英語](../../en/getting-started.md)と[中国語（簡体字）](../../zh/getting-started.md)で読めます：

- [はじめに](../../en/getting-started.md)：小さなプラグインを作り、zip からインストールする
- [API リファレンス](../../en/api.md)：manifest のフィールド、メソッド、イベント、各種の上限
- [権限](../../en/permissions.md)：各権限で何ができるか、どの権限と一緒に申請するか、インストール時にユーザーに何が表示されるか
- [アイランド](../../en/island.md)：macOS のメニューバーにあるアイランドにプラグインが何を表示できるか。コンポーネントごとに 1 ページ

プラグインには Hindsight 0.10.0 以降が必要です。

## プラグインを掲載する

プラグインや新しいバージョンは pull request で掲載します。手順、`plugins.json` のフィールド、審査で確認する点は [CONTRIBUTING.md](../../../CONTRIBUTING.md)（英語）を参照してください。

## テーマ

テーマで Hindsight の見た目を変えられます。[テーマサイト](https://hindsight.kyosweb.com/themes/)では、どのテーマもダウンロードする前にブラウザで試せます。ダウンロードしたら展開し、Hindsight の「設定 → 外観 → カスタムテーマ」で「テーマを読み込む」をクリックして `theme.json` を選びます。

- テーマの作り方：[Write a Hindsight theme](../../en/themes.md)（英語）
- テーマの掲載方法：CONTRIBUTING.md の [Themes](../../../CONTRIBUTING.md#themes)（英語）

テーマには Hindsight 0.10.2 以降が必要です。

## サードパーティのプラグイン

誰でも pull request でプラグインを提出できます。すべてのプラグインは審査を経てから掲載されます。リポジトリが `Tomotsugu-dev` の下にないプラグインはサードパーティのプラグインです。インストールの前に、公式のプラグインではなく、個人情報の漏えいにつながるおそれがあるという警告がユーザーに表示されます。

<h2 align="center">ライセンス</h2>

<p align="center">
  このリポジトリのプラグイン一覧は <a href="../../../LICENSE">MIT ライセンス</a>で公開しています。<br/>
  各プラグインは、それぞれのリポジトリのライセンスに従います。
</p>
