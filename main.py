import sys
import os
import platform
import warnings
import torch #提前加载torch以避免出现dll错误

# 忽略不必要的第三方库警告
warnings.filterwarnings("ignore", category=UserWarning, module="controlnet_aux")
warnings.filterwarnings("ignore", category=FutureWarning, module="timm")
warnings.filterwarnings("ignore", category=UserWarning, module="urllib3")

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from qfluentwidgets import setTheme, Theme

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gui import MainWindow

if __name__ == "__main__":
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)

    # 字体适配
    if platform.system() == "Darwin":
        font = QFont("Helvetica Neue")
        if not font.exactMatch():
            font = QFont("Arial")
        app.setFont(font)
    else:
        font = QFont("Microsoft YaHei UI")
        if not font.exactMatch():
            font = QFont("Segoe UI")
        app.setFont(font)

    setTheme(Theme.AUTO)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())