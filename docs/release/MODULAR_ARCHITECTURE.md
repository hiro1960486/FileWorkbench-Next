# FileWorkbench Next 3.0 RC Modular

## 方針
各機能を独立したQWidgetとして分離し、単体起動と統合起動の両方に対応します。

## モジュール
- modules/tree_module.py: 構成ツリーと4形式出力
- modules/rename_module.py: リネーム確認・実行
- modules/preview_module.py: 画像プレビューとファイル操作
- modules/compare_module.py: 左右比較と差分フィルター
- modules/hash_module.py: SHA256台帳と重複表示
- modules/common.py: 共通アイコン・ファイル操作・HASH

## 起動
- 統合: start_app.bat または python app_main.py
- 単体: python run_module.py tree
- 単体: python run_module.py rename
- 単体: python run_module.py preview
- 単体: python run_module.py compare
- 単体: python run_module.py hash

## 移行
旧統合版は app_main_legacy.py として保管しています。3.0 RCでは各モジュールの境界と単体動作を優先し、段階的に旧機能を移植します。
