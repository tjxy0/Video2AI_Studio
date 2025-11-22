import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from qfluentwidgets import setTheme, Theme

# 将当前目录添加到系统路径，确保可以正确导入 core 和 gui 模块
# 这对于打包后的 exe 运行也非常重要
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 从 gui 包中直接导入 MainWindow (利用 gui/__init__.py)
from gui import MainWindow

if __name__ == "__main__":
    # 1. 启用高DPI缩放 (针对 4K 屏幕及 Windows 缩放优化)
    # 注意：必须在创建 QApplication 实例之前调用
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    # 2. 创建应用程序实例
    app = QApplication(sys.argv)

    # 3. 设置主题
    # 使用深色模式 (Theme.DARK) 以符合专业 AI 软件的定位
    # 如果需要跟随系统，可以使用 Theme.AUTO
    setTheme(Theme.DARK)

    # 4. 启动主窗口
    window = MainWindow()
    window.show()

    # 5. 进入事件循环
    sys.exit(app.exec())