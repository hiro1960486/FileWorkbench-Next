"""他APPへプレビューモジュールを組み込む例。
実行: PYTHONPATH=src python examples/reuse_preview.py [ファイルパス]
"""
import sys
from PySide6.QtWidgets import QApplication,QMainWindow
from fileworkbench.modules.preview.interface import PreviewInterface
from fileworkbench.interfaces import ModuleContext,ModuleBox

app=QApplication(sys.argv)
# モジュール本体を直接操作せず、I/FからWidgetと入力を取得する。
port=PreviewInterface();window=QMainWindow();window.setCentralWidget(ModuleBox(port));window.resize(1100,800)
if len(sys.argv)>1:port.receive_context(ModuleContext(selected_paths=sys.argv[1:],source_module='example'))
window.show();app.aboutToQuit.connect(port.shutdown);sys.exit(app.exec())
