# Windows CI 実行準備

対象: 非公開 hiro1960486/FileWorkbench の専用 build/next-3.3-windows-20261008 ブランチ。

既存mainとは異なるFileWorkbench Next 3.3 RCのため、既存版のソースを上書きしない。
このソースZIPを build-input/next-source.zip として配置し、scripts/github_next_windows.yml をリポジトリの .github/workflows/next-windows.yml へ配置する。
専用ブランチへのpushまたはpull requestでWindows-2022 / Python 3.12 x64のビルドを実行する。
Artifacts: FileWorkbench-Next-Windows-validation。ZIP、SHA256、起動結果JSON、build.logを保存。
この設定は正式Releaseの公開・mainへのマージを自動で行わない。ビルド成功後も、ごみ箱・復元・メディア再生・D&D等のWindows操作確認を記録して正式版を判定する。

現在は送信許可待ちで、Windows CIは未実行。
