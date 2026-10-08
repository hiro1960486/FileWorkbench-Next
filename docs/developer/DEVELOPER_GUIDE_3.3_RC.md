# FileWorkbench Next 3.3 RC 開発者ガイド

更新日: 2026-10-09（日本時間）
対象コミット: `e876ead359957e48b0f7785a1b0b0b1ea60e3e0f`

## 対象版と旧資料

- 現行版は tree / rename / preview / compare / hash / recycle の6機能。
- 3.2.2開発者資料は docs/archive に原本を保存。
- 旧資料の8モジュール構成やServices引数付きI/Fは現行に適用しない。
- 履歴やプリセット関連処理の存在と、独立モジュールの登録は区別する。

## 起動・試験・ビルド

- 初回: scripts/setup_environment.bat
- 通常: start_app.bat
- 開発・保守: developer_mode.bat
- 単体: run_module.bat tree（ほか5つのIDも指定可能）
- 試験: scripts/run_tests.bat
- 配布作成: scripts/build_release.bat

## 検証環境と成果物

- Windows Server 2022 / Python 3.12.10 x64
- PySide6 6.8.3 / PyInstaller 6.22.3
- Send2Trash 1.8.3 / openpyxl 3.1.5 / pywin32 >=306
- EXE: dist/FileWorkbench_Next.exe
- ZIP: release/FileWorkbench_Next_3.3_RC_Windows_x64.zip
- 記録: build.log / release/exe-smoke.json

## ソースの責務

- app.py: 統合画面、ナビゲーション、モジュール配置
- module_registry.py: 宣言の探索、I/F生成、読込失敗の表示
- interfaces/: 契約、アダプター、イベントバス、対象の配送
- modules/<id>/: module.py / interface.py / module.json
- services/: ファイル操作、命名、ごみ箱、対象共有、再生
- core/: 既存のツリー・比較・HASH等の再利用処理

## モジュールの宣言と登録

- 宣言は各モジュールフォルダーの module.json に置く。
- IDとフォルダー名を一致させる。interface_entrypointからI/Fを読み込む。
- <Id>Interface()を引数なしで生成し、descriptor一致を確認する。
- 標準表示順は MODULE_ORDER。新しいIDは追加分として後ろに並ぶ。
- 読込失敗はUnavailableModuleとして画面と保守診断に残す。

## 共通I/F契約

- ModuleDescriptor: ID、版、入力、能力、コマンド、イベントの宣言
- ModuleContext: selected_paths / working_directory / options / source_module
- ModuleEvent: name / source / payload
- ModulePort: create_widget / receive_context / current_context
- execute / subscribe / shutdown
- WidgetModuleAdapterがウィジェット生成と通知を仲介する。

## 対象共有とイベント配送

- ContextRouterが共通対象と個別対象を管理する。
- 共有を有効にする前の個別状態を保存し、無効化時に戻す。
- treeのselection.changedを共通対象へ反映する。
- preview.requested / rename.requestedを対応するI/Fへ配送する。
- 移動・削除・リネーム前のfiles.will_changeでプレビューを解放する。
- 他モジュールのウィジェットを直接操作する連携は避ける。

## 開発・保守画面

- 組み込み試験: 統合に近いModuleBoxへ配置
- 単体ウィンドウ: 独立したI/Fとウィジェットを生成
- 契約試験: 独立I/Fで宣言一致、通知、未対応拒否、終了を確認
- 入力コンテキストJSON: 選択中のI/Fへ送信
- 保守診断: Python、OS、依存版、モジュール読込状態
- 診断・ログ保存: イベントを含むJSON。新規ファイルとして保存

## HASHの入力経路

- 画面の対象欄とD&Dはファイル・フォルダーを受け取る。
- HashInterface.receive_contextの入力は現在フォルダーに限定する。
- module.jsonのaccepted_inputsもfolderを宣言する。
- 画面の入力能力とI/F契約を同じものとして扱わない。
- I/F例: HashInterface()、ModuleContext(selected_paths=[フォルダー])

## ごみ箱の検索

- services/recycle_bin.pyがWindows Shell.Applicationを使用する。
- 現在ユーザーのShellごみ箱を検索する。
- 名前・元の場所・削除日時等で一覧を絞り込む。
- 失敗はメッセージと状態欄に表示。取得件数と表示件数を分ける。
- 退避履歴の読込失敗がWindowsごみ箱検索を止めない。
- クラウドWebごみ箱・NAS削除履歴の横断検索は未実装

## ごみ箱の復元と退避

- I/Fのコマンドはsearch / restore。ごみ箱内プレビューは提供しない。
- 任意の既存フォルダーを復元先として指定できる。
- 元の場所がなく、復元先も未指定なら指定を求める。
- 同名はスキップまたは別名。Shellで.fwn_restore_*へ復元する。
- コピーとfingerprint照合後も退避コピーを保持する。
- 失敗時も退避先を残し、その場所をエラーに表示する。

## D&DとPDFの修正

- PathEditでDragEnter、DragMove、Dropの受け取りを継続する。
- フォルダー専用欄へファイルを置いた場合も親へ渡さず説明する。
- 一覧ビューポートとモジュール本体にもDragMove処理を加えた。
- 生成EXEでtree / hash / recycleの下部指定欄を確認した。
- PDF終了時はclose、親の切離し、参照解放でロックを解放する。
- ごみ箱用win32timezoneをPyInstallerのhidden-importへ追加

## 試験結果と確認の境界

- 2026年10月8日のWindows自動試験57件が成功。
- 対象パターンはtest_module*.py。旧一体型のtest_app.pyは除外する。
- 生成EXEの起動、6モジュール、同梱資源を確認した。
- 実Windowsごみ箱検索と一覧表示、Qt D&Dイベント配送も成功。
- Explorerからの物理D&D、ごみ箱復元の全操作、メディアの受入は継続。
- 自動試験の成功だけで正式版・全操作完了とはしない。

## ビルドと自己試験

- build_windows.pyが依存導入、compileall、現行試験を実行する。
- PyInstallerはonefile / noconsole。assets、docs、module.jsonを同梱。
- 生成EXEを--smoke-test REPORTで起動し、資源と読込状態を検証する。
- --dd-self-testはQtイベント配送を追加する。
- --recycle-self-testは試験用ファイルを実際にごみ箱へ移す。
- 最後のフラグは専用試験環境で使用し、通常起動に付けない。

## 公開管理と次の受入確認

- 公開先はFileWorkbench-Next。旧FileWorkbenchは別リポジトリ。
- ソースとdocsをGit管理し、EXE・.venv・build・dist等は除外する。
- EXE配布はReleasesで別管理。現時点では未登録。
- Windows 11で下部欄・比較左右・切離し画面のD&Dを確認する。
- 任意先復元、同名、元フォルダーなし、失敗時退避先を確認する。
- PDF解放、音声・動画シーク、ライト／詳細リネームを受入確認する。

## I/F入力例

開発者モードでtreeを選び、次のJSONを入力して「I/Fへ送信」を押す。パスは存在する試験フォルダーに置き換える。

```json
{"selected_paths":["C:/FWN_Test"],"working_directory":"","options":{},"source_module":"developer"}
```

## 現行宣言一覧

| ID | 入力宣言 | I/Fコマンド |
| --- | --- | --- |
| tree | folder | scan, export, filter, refresh |
| rename | files, folder | refresh, preview, rename, configure |
| preview | files | refresh, next, previous, release, play, pause, stop, seek |
| compare | left_folder, right_folder, left_path, right_path, files | compare, filter, refresh |
| hash | folder | scan, filter, export, refresh |
| recycle | folder, query, destination | search, restore |

## 根拠と資料の優先順位

現行ソースのmodule_registry.py、interfaces、各module.json/interface.py、services/recycle_bin.py、developer/workbench.py、scripts/build_windows.pyを照合した。実装変更時は宣言・I/F・試験・本ガイドを同時に見直す。

Windows試験の記録はdocs/release/DD_ROUTING_FIX_20261008.md、DD_WINDOWS_BUILD_LOG_20261008.txt、RECYCLE_SEARCH_FIX_20261008.mdを参照。CI記録は旧非公開リポジトリ側にあるため、公開閲覧者にはログ文書を案内する。公開リポジトリ自身でCIを実行したという意味ではない。

3.2.2資料はdocs/archiveの履歴資料として残す。古い資料の試験数や完了表現を現行の受入結果へ転用しない。
