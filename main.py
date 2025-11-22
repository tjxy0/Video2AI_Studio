import sys
import os
import platform
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from qfluentwidgets import setTheme, Theme

# 将当前目录添加到系统路径，确保可以正确导入 core 和 gui 模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 从 gui 包中直接导入 MainWindow
from gui import MainWindow

if __name__ == "__main__":
    # 1. 启用高DPI缩放 (针对 4K 屏幕及 Windows 缩放优化)
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    # 2. 创建应用程序实例
    app = QApplication(sys.argv)

    # 3. 字体适配 (解决 macOS 下 Segoe UI 缺失警告)
    if platform.system() == "Darwin":  # macOS
        font = QFont("SF Pro Text")
        if not font.exactMatch():
            font = QFont("Helvetica Neue")
        if not font.exactMatch():
            font = QFont("Arial")
        app.setFont(font)

    # 4. 设置主题
    setTheme(Theme.DARK)

    # 5. 启动主窗口
    window = MainWindow()
    window.show()

    # 6. 进入事件循环
    sys.exit(app.exec())