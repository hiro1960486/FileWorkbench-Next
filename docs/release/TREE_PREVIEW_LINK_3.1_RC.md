# Ver.3.1 RC — Tree → Preview 連携修正（2026-10-07）

## 変更点
- TreeModuleの選択変更をTreeInterfaceでselection.changedへ変換し、EventBusへ発行。
- ContextRouterがtree由来のイベントだけを受け、ModuleContext(source_module="tree")をpreview.receive_contextへ配送。
- Previewはファイルリストとindexを初期化して表示。空選択、フォルダー、存在しないファイルでは古い表示をクリア。
- User ModeをModulePort経由で組み立てるよう変更。Developer Modeにも同じRouterを使用。
- Developer Event Logに時刻・送信元・イベント名・宛先を表示。context.routed、受信イベントも記録。
- Developerの単体ウィンドウも登録済みPortのWidgetを利用して、連携対象とする。
- tree / previewのI/F版を1.1に更新。アプリ本体は3.1 RCを維持。依存関係追加なし。

## 起動・操作確認
1. requirements.txtの依存関係を導入し、start_app.batで起動。
2. 構成ツリーで対象フォルダーを開き、画像ファイルを選択。
3. 左側の「プレビュー」を押すと選択画像が表示される（画面の自動切替は行わない）。
4. 別のファイルを選び、プレビューが更新されることを確認。
5. developer_mode.batではtreeを組み込み、ファイルを選択後previewを組み込み。Event Logを確認。

## 通信仕様（引継ぎ仕様書の追補）
selection.changed: source="tree", payload={"selected_paths": [文字列パス,...]}。
RouterはpreviewへModuleContextを送る。空リスト・フォルダーも配送し、Preview側で表示対象を判定。
context.routed: source="router", payloadにsource_module / destination / selected_pathsを含む。
不正なpayloadや配送失敗はmodule.errorを記録。preview自身のイベントは再配送しない。
複数パスの入力では入力順に保持し、先頭を表示。前後移動が使用可能。

## 試験結果
Linux / Python 3.12 / PySide6、QT_QPA_PLATFORM=offscreenで新規回帰試験6件成功。
- 全5モジュールの必須I/FとModuleBox生成・表示。
- 画像選択・選択切替・context.received・context.routed。
- フォルダー／ルート選択・選択解除と表示クリア。
- 複数パス、前後移動、存在しないパス、非画像表示。
- ループ防止、不正payloadのエラー通知。
- User Mode / Developer Mode起動、単体ウィンドウ、tree・preview組み込み、ログ確認。
全Pythonファイルの構文解析、ZIP再展開後の同試験、SHA256一致確認を実施。
通常画面を画像にしてプレビューの表示を確認。環境の日本語フォント不足によりラベルの字形は目視検証対象外。

## 残課題・試験範囲
Windows実機操作、EXE生成・EXE起動は未実施。本ZIPは修正済みソース一式。
既存tests/test_app.pyは旧統合版用で、現行app_mainから旧クラスをimportするためそのまま実行できない。今回の試験はtest_module_link.pyを使用。
旧統合版からの全機能移植、依存不足の個別隔離、Studioレイアウト、既存ビルドスクリプトの版数・パス整備は今回の対象外。
原本DOCX/PDFは引継ぎ資料として保持し、本追補を最新実装の説明とする。
破壊的操作のコードは変更せず、試験には一時フォルダーのみ使用。
