# ごみ箱検索 修正 2026-10-08

原因: EXEにwin32timezoneが含まれず、ごみ箱の削除日時の読込で No module named 'win32timezone' が発生していた。
修正: PyInstallerのhidden-importへwin32timezoneを追加。
検索失敗はダイアログと画面内の両方へ表示。取得件数と表示件数を分けて表示。
検索条件をクリアするボタンを追加。期間入力の変更を一覧へ即反映。
退避履歴の読込に失敗してもWindowsごみ箱の検索を続ける。

Windows Server 2022 / Python 3.12.10 x64 / PySide6 6.8.3で50件の現行モジュール試験成功。
生成EXEで、一時テストファイルをWindowsごみ箱へ送り、バックグラウンド検索で取得し、画面の一覧に1件表示できることを確認。
起動確認と資料・アイコン確認も成功。ごみ箱からの復元やメディア全操作の実機受入は別途必要。
成功記録: https://github.com/hiro1960486/FileWorkbench/actions/runs/37771921026
ソースコミット: 242ae3eab0cdfbc0dd445a7cb09d6fa19db3cbfc（build-input内の修正ファイルを適用）

起動: ZIPをすべて展開しFileWorkbench_Next.exeをダブルクリック。
確認: ごみ箱・復元 → 検索条件をクリア → 検索・一覧更新。
