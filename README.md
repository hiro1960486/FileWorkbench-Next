# FileWorkbench Next

Windows向けのファイル作業アプリ。開発中の **3.3 RC** を公開しています。

構成ツリー、プレビュー、一括リネーム、左右比較、SHA256一覧、ごみ箱検索・復元を、縦型ナビゲーションと共通の対象指定で利用できます。機能別モジュールとI/Fを分け、単体起動と保守診断にも対応しています。

## 起動する

ソースからの起動には64ビットPythonが必要です。検証環境はPython 3.12です。

1. `scripts/setup_environment.bat` を実行して依存パッケージを導入します。
2. `start_app.bat` を実行します。

ビルド済みZIPを入手した場合は、すべて展開して `FileWorkbench_Next.exe` を起動します。Pythonの導入は不要です。

## ビルドする

`scripts/build_release.bat` を実行します。環境作成、現行モジュール試験、PyInstallerによるEXE生成、生成EXEの起動検証、配布ZIPとSHA256生成を行います。

- EXE: `dist/FileWorkbench_Next.exe`
- 配布ZIP: `release/FileWorkbench_Next_3.3_RC_Windows_x64.zip`
- 記録: `build.log`

## 確認済みの内容

2026-10-08にWindows Server 2022 / Python 3.12.10 x64 / PySide6 6.8.3で現行モジュールの自動試験57件に成功しました。生成EXEの起動、6モジュールと同梱資源、実Windowsごみ箱の検索・一覧表示、下部指定欄へのD&Dイベント配送を確認しています。

- ごみ箱検索に必要な `win32timezone` の同梱を修正。
- PDF終了後のWindowsファイルロックを修正。
- 指定欄・一覧のドラッグ移動時の受け取りを修正。

詳細は `docs/release/DD_ROUTING_FIX_20261008.md` と `docs/release/RECYCLE_SEARCH_FIX_20261008.md` を参照してください。

## 開発中の範囲

正式版ではありません。利用者のWindows 11環境でのExplorerからのD&D、ごみ箱復元、音声・動画再生等の全操作の受入確認は継続中です。

ごみ箱検索は現在のWindowsユーザーのShellごみ箱を対象にします。NASやクラウドサービスのWebごみ箱を横断検索する機能はありません。

旧一体型向け `tests/test_app.py` は現行モジュール試験に含めません。古い資料・チェックリストは作成時点の記録であり、最新の修正記録を優先してください。

## 開発・保守

- `developer_mode.bat`: 開発・保守画面
- `run_module.bat tree`: 構成ツリーの単体起動（preview / rename / compare / hash / recycleも指定可能）
- `scripts/run_tests.bat`: 現行モジュール試験

機能本体は `src/fileworkbench/modules/`、共通I/Fは `src/fileworkbench/interfaces/`、再利用処理は `src/fileworkbench/services/` にあります。

不具合報告には、使用版、操作手順、期待結果、実際の結果を添えてください。ログや画像を公開する前に、個人のパスやファイル名を確認してください。

## ライセンス

MIT License。詳細は [LICENSE.txt](LICENSE.txt) を参照してください。依存ライブラリにはそれぞれのライセンスが適用されます。

## 開発者向け資料

現行3.3 RCの[開発者ガイド](docs/developer/DEVELOPER_GUIDE_3.3_RC.md)と[PowerPoint版](docs/developer/FileWorkbench_Next_3.3_RC_Developer_Guide.pptx)を公開しています。モジュールI/F、開発・保守、ビルド、試験結果と未確認範囲を説明しています。

[3.2.2 RC 開発者ガイド（PowerPoint）](docs/archive/FileWorkbench_3.2.2_Developer_Guide.pptx)を参考資料として保存しています。現行3.3 RCとの違いは[対象版と対応表](docs/archive/README.md)をご確認ください。

現在の仕様はソースのmodule.json・interface.pyとdocs/release内の最新修正記録を優先してください。

## 正式な管理先と整理方針

[3プロジェクトの役割・移行順序・未完了条件](docs/REPOSITORY_CONSOLIDATION_20261010.md)を参照してください。再利用部品はModuForge、Nextの統合アプリと配布はFileWorkbench-Next、従来版の履歴はFileWorkbenchで管理します。管理先の統一と正式版リリースの判定は別です。

### 当面の独立開発方針

ModuForgeとFileWorkbench-Nextは、当面それぞれ独立して開発・試験・版管理を進めます。現段階で部品の同期や取り込み、版の連動は行いません。ModuForgeのモジュール・APIが整った後、必要な部品をNextへ組み込む作業を別途行います。
