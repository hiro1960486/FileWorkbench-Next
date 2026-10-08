"""安全なコピーの利用例。実行: PYTHONPATH=src python examples/reuse_file_service.py"""
from pathlib import Path
from tempfile import TemporaryDirectory
from fileworkbench.services.file_operations import FileOperationsService

# APPごとに専用の設定・退避領域を指定する。
# この例では一時フォルダーだけを使い、実データは操作しない。
with TemporaryDirectory() as temporary:
    root=Path(temporary);source=root/'sample.txt';source.write_text('Sample',encoding='utf-8')
    destination=root/'output';destination.mkdir()
    service=FileOperationsService(root/'my_app_state')
    # コピーは既存先を上書きせず、内容を照合する。
    for result in service.perform('copy',[source],destination):
        print(result.status,result.target,result.error)
