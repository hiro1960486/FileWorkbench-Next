# Windows ビルド確認 2026-10-08

Windows Server 2022 / Python 3.12.10 x64 / PySide6 6.8.3。
現行モジュール自動試験47件成功。PyInstallerでWindows EXE生成成功。
生成EXEの起動確認をビルド内と生成後に実施し、いずれも成功。
tree / rename / preview / compare / hash / recycle の6機能を読み込み。
利用不可モジュール、欠落資料、欠落アイコンは0件。
Windowsで発見したPDF終了後のファイルロックを修正し、終了直後の変更・削除の回帰テストに成功。

EXEはWindows上で確認済み。ただし実ユーザー環境でのD&D、ごみ箱復元、音声・動画再生などの全受入確認は未実施のため、版番号は3.3 RCを維持。
既存一体型用 tests/test_app.py は現行モジュールの47件には含まれない。

GitHub確認: https://github.com/hiro1960486/FileWorkbench/actions/runs/37766610311
ソースコミット: 479434cecbc180d5ab88f21039e0f5cf2bd13516

ZIPをすべて展開して FileWorkbench_Next.exe をダブルクリック。
Pythonの導入やBATの実行は不要。
