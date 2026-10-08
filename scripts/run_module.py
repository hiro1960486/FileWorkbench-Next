import argparse,importlib,sys
from PySide6.QtWidgets import QApplication
parser=argparse.ArgumentParser();parser.add_argument('module',choices=('tree','rename','preview','compare','hash','recycle'))
ns=parser.parse_args();app=QApplication(sys.argv)
module=importlib.import_module('fileworkbench.modules.'+ns.module+'.interface')
port=getattr(module,ns.module.capitalize()+'Interface')();w=port.create_widget();w.show()
app.aboutToQuit.connect(port.shutdown)
sys.exit(app.exec())
