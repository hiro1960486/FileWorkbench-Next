# 過去版の開発資料

[FileWorkbench 3.2.2 Developer Guide](FileWorkbench_3.2.2_Developer_Guide.pptx) は61枚の開発者向け詳細仕様書です。対象は3.2.2 RC、基準コミットは bc7e3dc3f6fd2f81cb61fbb4b32ba9da82c908af です。原本は変更していません。

今回公開する3.3 RCの最新仕様書としては扱いません。資料に載るファイル・クラス・コマンド・実装例には現行ソースと異なるものがあります。

| 項目 | この参考資料 | 公開予定の3.3 RCソース |
|---|---|---|
| 登録する機能 | tree / rename / preview / compare / hash / history / recycle / presets | tree / rename / preview / compare / hash / recycle |
| 宣言ファイル | config/modules/*.json | src/fileworkbench/modules/*/module.json |
| HashInterface生成 | HashInterface(services) | HashInterface() |
| ごみ箱コマンド | refresh / preview / restore / cancel | search / restore |
| ごみ箱実装の説明 | recycle_index.py等の分割構成 | services/recycle_bin.pyのWindows Shellアダプター |
| 試験 | 資料の対象ソースに対応する試験 | 現行はtests/test_module*.pyの57件 |

3.3 RCでは履歴情報を扱う処理はありますが、historyとpresetsという独立モジュールは登録していません。資料の説明を、そのまま現行版の実装済み機能として読まないでください。

現行の契約は src/fileworkbench/interfaces/contracts.py、宣言は各module.json、コマンドは各interface.pyを参照してください。最新のWindows確認結果はdocs/release/DD_ROUTING_FIX_20261008.mdにあります。
