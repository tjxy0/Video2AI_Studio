from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt
from qfluentwidgets import FluentWindow, FluentIcon as FIF, InfoBar, InfoBarPosition

from core.config import GenerationConfig
from core.env_checker import EnvironmentChecker
from gui.home_interface import HomeInterface
from gui.setting_interface import SettingInterface


class MainWindow(FluentWindow):
    """
    主应用程序窗口：组装各个子界面
    """

    def __init__(self):
        super().__init__()

        # 初始化配置
        self.config = GenerationConfig()

        # 窗口基础设置
        self.setWindowTitle("Video2AI Studio - 视频风格化工作台")
        self.resize(1000, 750)
        # 建议在 assets 文件夹放入 icon.png
        # self.setWindowIcon(QIcon("assets/icon.png"))

        # 创建子页面
        self.homeInterface = HomeInterface(self.config, self)
        self.settingInterface = SettingInterface(self.config, self)

        # 添加到导航栏
        self.addSubInterface(self.homeInterface, FIF.HOME, "工作台")
        self.addSubInterface(self.settingInterface, FIF.SETTING, "设置")

        # 执行启动自检
        self._run_startup_checks()

    def _run_startup_checks(self):
        """应用启动时的环境诊断 (报告 7.1)"""

        # 1. 检查 FFmpeg
        if not EnvironmentChecker.check_ffmpeg():
            InfoBar.error(
                title='环境严重缺失',
                content='未检测到 FFmpeg！无法进行视频拆帧和合成。请安装 FFmpeg 并将其添加到系统 PATH。',
                orient=Qt.Orientation.Horizontal,
                isClosable=False,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=-1,
                parent=self
            )

        # 2. 检查 CUDA
        if not EnvironmentChecker.check_cuda():
            InfoBar.warning(
                title='GPU 加速不可用',
                content='未检测到 NVIDIA 显卡或 CUDA 环境。程序将无法运行或运行极慢。',
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=5000,
                parent=self
            )
        else:
            # 显示当前显卡信息
            gpu_name = EnvironmentChecker.get_cuda_info()
            InfoBar.success(
                title='GPU 就绪',
                content=f'已连接至: {gpu_name}',
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=3000,
                parent=self
            )