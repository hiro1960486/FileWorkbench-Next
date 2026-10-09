# FileWorkbench Next v3.3.0-rc1 — プレリリース案内

> 開発評価版（Pre-release）。正式版ではありません。

## 概要
Windows向けファイル作業アプリ「FileWorkbench Next」3.3 RCの初回評価用リリースです。

## 主な機能
- 構成ツリーとファイルプレビュー
- 一括リネーム、左右比較、SHA256一覧
- Windowsごみ箱の検索・一覧表示・復元機能
- 縦型ナビゲーション、共通対象指定
- モジュール単体起動と開発・保守モード

## 既存の検証記録
2026-10-08時点のリポジトリREADMEによれば、Windows Server 2022 / Python 3.12.10 x64 / PySide6 6.8.3で現行モジュールの自動試験57件に成功。生成EXEの起動、モジュール・同梱資源、ごみ箱検索・一覧、指定欄へのD&Dイベント配送を確認。

## 未確認・制限
- Windows 11実機でのExplorerからのドラッグ＆ドロップ、ごみ箱復元、音声・動画再生などの一連の受入試験は継続中です。
- Windowsごみ箱は現在のWindowsユーザーのShellごみ箱が対象です。NASやクラウドWebごみ箱の横断検索には対応しません。
- 重要なファイルはバックアップし、移動・改名・復元などの操作はテストデータで検証してください。

## 利用方法
**ソースから実行**: 64ビットPython（検証環境3.12）を準備し、`scripts/setup_environment.bat`、続いて`start_app.bat`を実行します。

**配布ZIPから実行**: ビルド済みZIPがリリースに添付された場合、ZIP全体を展開して`FileWorkbench_Next.exe`を起動します。ZIPが添付されていなければEXE配布はまだありません。

**ローカルビルド**: `scripts/build_release.bat`。成功時の成果物は`release/FileWorkbench_Next_3.3_RC_Windows_x64.zip`です。成果物を添付する前に動作確認とSHA256照合を推奨します。

## 開発資料
- [README](../../README.md)
- [開発者ガイド](../developer/DEVELOPER_GUIDE_3.3_RC.md)
- [最新の修正記録](./)

## 公開前確認
- [ ] 対象コミットとタグ `v3.3.0-rc1` の一致
- [ ] ビルドログと自動試験結果の確認
- [ ] 配布ZIPの存在・解凍・EXE起動・SHA256照合
- [ ] Pre-release設定で公開
