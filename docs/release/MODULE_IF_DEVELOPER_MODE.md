# モジュール・ボックスI/Fと開発者モード

各モジュールフォルダーは次を持ちます。
- `module.py`: 機能UI本体
- `interface.py`: メイン土台とのボックスI/F
- `module.json`: ID、表示名、アイコン、入力、能力の宣言

共通契約は `src/fileworkbench/interfaces/contracts.py` にあります。
- `ModuleDescriptor`: モジュールの自己記述
- `ModuleContext`: メインからモジュールへの入力
- `ModuleEvent`: モジュールからメインへの通知
- `ModulePort`: create_widget / receive_context / execute / subscribe / shutdown

`ModuleBox` が機能UIを箱として包み、統合画面へ配置します。

## 開発者モード
`developer_mode.bat` で起動します。
- module.json相当のI/F情報を表示
- 選択モジュールをボックスとして組み込み
- 独立ウィンドウで単体起動
- JSONでModuleContextを入力
- I/F契約試験
- イベントログ表示
