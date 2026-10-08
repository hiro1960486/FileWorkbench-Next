FileWorkbench Next Ver.3.3 RC — 保守性改善版

開発派生版: 3.3 RCを基に、Windowsのシンボリックリンク権限に左右される自動試験を修正しています。
日本語テキストのCP932/UTF-8判定も修正しています。製品機能の変更ではなく、Windows実機での再ビルド・全試験確認前の開発中ソースです。

初回のみ:
  scripts\setup_environment.bat
  Python環境(.venv)を作成しrequirements.txtを導入します。

通常起動:
  start_app.bat
開発・連携確認:
  developer_mode.bat
単体起動（コマンドプロンプトで実行）:
  run_module.bat tree
  run_module.bat preview
  run_module.bat rename
  run_module.bat compare
  run_module.bat hash

BATの起動順はありません。初回セットアップ後、用途に合ったBATを選びます。
すべての入口は共通のscripts\launch.batを使い、.venvを優先します。
失敗時は終了コードを表示し、画面を閉じずにエラーを確認できます。

連携確認:
  構成ツリーでフォルダーを開く → 画像を選択 → 左の「プレビュー」を開く。
  フォルダー選択・選択解除では古いプレビューをクリアします。
  Developer Modeではtreeとpreviewを組み込み、ログで配送を確認できます。

自動試験:
  scripts\run_tests.bat
Windows EXE生成:
  scripts\build_release.bat
  出力: dist\FileWorkbench_Next.exe
        release\FileWorkbench_Next_3.3_RC_Windows_x64.zip
        release\SHA256_RELEASE.txt
        build.log
  配布ZIP内にEXEのSHA256を記録します。

構造:
  src/fileworkbench/modules/<機能>/module.py : 各UI・機能
  interface.py : その機能の入力・コマンド・イベント・接続
  module.json : 登録情報・対応入力・コマンド・イベント
  interfaces/adapter.py : UI寿命とイベント通知のみ
  interfaces/context_router.py : モジュール間の配送
  module_registry.py : 宣言から読込、失敗時に個別の利用不可表示
  docs / scripts / tests / legacy : 資料・補助処理・試験・移植元

最新仕様・変更点・制限:
  docs/release/ARCHITECTURE_3.3_RC.md
原本引継ぎDOCX/PDFは3.1 RC時点の資料です。今回の追補を優先してください。
本版はRCです。Windows実機とEXE生成は未確認です。
今回の派生修正も、Windows実機での再ビルドと試験は未確認です。

3.3 RC拡張:
- ごみ箱・復元: Windowsごみ箱の検索、復元先指定、同名保護、退避履歴の復元。
- 右クリック: コンテンツ別メニュー、コピー・移動・複製・ごみ箱・情報等。
- 各画面DD、Ctrl/Shift複数選択、User Modeの全コンテンツの切り離し・復帰。
- 画像/PDF/テキスト/Office本文/ZIP一覧/音声・動画プレビュー。
- 再生・一時停止・停止・可変シーク・音量は下部へ配置。
- 他APP再利用: services内のI/Fとexamplesを参照。
- Windows専用機能の実機確認は未実施。旧版の全機能移植は未完了です。

追加:
- 共通対象欄と各コンテンツの「共通対象を使う」。外せば個別指定へ復帰。
- 各列は境界ドラッグで幅変更、見出しクリックでソート。
- 比較の左右対象はDDと交換に対応。ファイル同士も比較可能。
- リネームはライト／詳細切替、連番・日付・正規表現等。
- Developer Modeは独立単体起動、独立契約試験、保守診断、診断ログ保存。
- 現行モジュール自動試験47件成功（Linux）。

2026-10-08 ビルド準備更新:
  Qt・ビルド依存を固定。生成EXEの起動確認をビルド工程に追加。
  詳細: docs/release/BUILD_VERIFICATION_20261008.md
  Windowsビルドは未実施のため、本版は引き続きRCです。

Windowsビルド確認（2026-10-08）: 47件成功、EXE生成・起動成功。
最新記録: docs/release/WINDOWS_BUILD_RESULT_20261008.md
全操作の受入確認は未完了のため3.3 RCを維持します。

ごみ箱検索修正（2026-10-08）: win32timezone同梱、検索失敗のダイアログ表示、条件クリアを追加。
Windowsで50件成功、生成EXEで実ごみ箱の検索・一覧表示成功。
最新記録: docs/release/RECYCLE_SEARCH_FIX_20261008.md

D&D修正（2026-10-08）: 指定欄と一覧のドラッグ移動時の受け取りを修正。
Windows57件成功、生成EXEで下部指定欄と実ごみ箱検索・一覧表示の確認成功。
最新記録: docs/release/DD_ROUTING_FIX_20261008.md
