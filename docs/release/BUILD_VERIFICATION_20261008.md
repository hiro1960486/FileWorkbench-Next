# ビルド確認 2026-10-08

- Linux / Python 3.12 / PySide6 6.8.3: 現行モジュールの自動試験47件成功、正常終了。
- ソース起動試験: tree / rename / preview / compare / hash / recycle の6機能を読み込み。利用不可モジュールと欠落資料・アイコンは0件。
- Qt 6.12.0では試験成功後にプロセスが異常終了したため、正常終了した6.8.3に固定。
- ビルドには生成EXEの起動試験を追加。失敗・90秒超過・確認結果欠落なら配布ZIPを生成しない。
- Windows EXEの生成・起動、およびWindowsごみ箱の実機確認は未実施。正式版ではない。
- tests/test_app.py は旧一体型App用で、現行のapp_main.pyと互換性がないため試験対象外。47件は現行モジュールの試験件数。
- GitHub送信は自動承認審査が拒否。送信先の明示的な許可後にWindows CIを実行する。

Windowsでの実行: scripts\build_release.bat。初回環境作成から試験、EXE生成、起動確認、配布ZIP・SHA256生成まで実行する。
