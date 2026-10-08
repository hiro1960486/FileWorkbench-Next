# FileWorkbench Next 3.2 RC — 構造改修・仕様追補

2026-10-07 / Author: hiro1960 / MIT

## 目的と変更
共通部に機能別の判断が集まる状態を減らし、変更範囲を明確にする。
共通AdapterはWidget生成・終了、Context保持、イベント購読と明示コマンドの配送に限定。
load/files/previewなどを探して処理を推測する分岐を削除。
各interface.pyがapply_context、commands、必要なWidgetのsignal接続を担当する。
preview本体はset_files(paths)というファイル入力を受け、共通Contextの解釈はI/Fが行う。

module.jsonを登録情報の正とし、Descriptorをそこから生成。
interface_entrypoint、commands、emitted_events、accepted_inputsを実装と一致させた。
アプリ3.2 RC、各I/F 1.2。依存ライブラリ追加なし。
単体起動は選択されたI/Fのみをimportする。
統合時は個別にimportし、失敗したモジュールは利用不可表示として残す。
他の機能とDeveloper Modeは起動できる。未対応コマンドで任意のWidgetメソッドは呼べない。

Developer Modeはmodule_idごとに1つのBoxを維持。
単体表示と組み込みは同じPort/Widgetを移動して利用する（独立した複製ではない）。
別窓ボタンはクリックしたBoxのモジュールを開く。閉じた別窓は再表示または組み込み可能。
契約試験で読み込みエラーをNG表示。組み込み・単体起動時の例外もログに表示。
終了時はPortを閉じて破棄。二重shutdownが可能。再生成時にsignal接続も作り直す。
Contextは送受信時にコピーし、外部からの変更で内部状態が変わらないようにした。

BATのPython選択とエラー表示をscripts/launch.batへ統一。
setup_environment.batで初回環境を作成し、全BATで同じ.venvを優先。
ビルドの作業ルートをプロジェクト直下へ修正。旧2.7系の存在しないファイル参照を削除。
PyInstallerへsrc、動的モジュール、module.json、assets、docsを含める。
package_release.pyでEXEハッシュ入りZIPとZIPハッシュを作る。

## 通信と入力
Tree selection_changed(list[str]) → TreeInterface selection.changed → EventBus → ContextRouter → PreviewInterface.receive_context。
Routerはtreeからpreviewへの配送だけを行う。UI切替やファイル解釈は行わない。
イベント全体の監視を先に通知し、元イベントより配送イベントが先にログへ出る問題を修正。

- tree: selected_pathsの先頭フォルダー、ファイルの親、またはworking_directoryをロード。空Contextはクリア。
- preview: selected_paths中の存在するファイルを入力順で表示。フォルダー・空入力はクリア。
- rename: ファイル群、フォルダー内のファイル群、working_directoryを変更候補へ入力。入力だけではリネームしない。
- compare: options.left_folder / right_folder、またはselected_pathsの先頭2フォルダー。比較はcompareコマンドで実行。
- hash: selected_pathsの先頭フォルダー、またはworking_directoryをスキャン対象として設定。入力だけでは計算しない。
  複数ファイル入力は未対応のためaccepted_inputsからfilesを除外。将来の追加時はI/F・宣言・試験を同時更新。

各module.jsonのcommandsが実行可能コマンド一覧。既存の確認・保存ダイアログを使用するコマンドもある。
context.received / command.completed / module.errorは全I/Fの共通イベント。
treeのみselection.changedを追加。実装されていない処理完了イベントの宣言を削除した。

## 検証
Linux / Python 3.12 / PySide6 / offscreenで16件成功。
前版の連携6件と構造回帰10件。内容はtests/test_module_link.py、test_module_architecture.py。
- 全I/F・ModuleBox生成、画像選択・切替・クリア・複数入力・前後移動。
- 通常画面とDeveloper Mode起動、単体表示と組み込み。
- previewのimport失敗を模擬して両モードとtreeの継続を確認。
- registry import時に機能モジュールが読み込まれないことを別プロセスで確認。
- 宣言・Descriptor・対応コマンドの一致。
- Contextコピー、未対応コマンド拒否、rename/compare/hash入力処理。
- 二重終了と再生成、購読の重複防止と解除。
- Box重複防止、選択中モジュールに依存しない切り離し、再組み込み。
- イベント順序、ビルド引数・manifest同梱指定、テスト用ダミーEXEでZIP/ハッシュ生成。
全Pythonファイル構文解析、納品ZIPの再展開試験、ソースハッシュ照合も実施。
試験用ファイルは一時フォルダーのみ。実データや破壊的操作は使っていない。

## 残課題と次の作業
Windows実機操作、BAT実行、実EXEの生成と起動は未確認。
ダミーEXEを使ったパッケージ試験は、実EXEが起動する証明ではない。
構造改修は完了したが、旧統合版の機能をすべて移植した完成版ではない。
重いHASH/比較/走査のバックグラウンド化、リネームの途中失敗回復・永続Undo、previewの安全なコピー/移動、メディア機能は次の機能改善対象。
既存tests/test_app.pyは旧統合版用で現在の入口とは不整合。今回のrunnerはtest_module*.pyを実行する。
旧DOCX/PDF・過去のrelease資料は履歴として保持。本追補が現在の構造の説明。
次はWindowsでセットアップ→通常起動→連携確認→EXEビルドを確認し、その後機能ごとの安全性と旧版機能差分を埋める。
