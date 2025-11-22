from PyQt6.QtCore import Qt
from qfluentwidgets import FluentWindow, FluentIcon as FIF, InfoBar, InfoBarPosition
from core.config import GenerationConfig
from core.env_checker import EnvironmentChecker
from gui.home_interface import HomeInterface
from gui.setting_interface import SettingInterface


class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        self.config = GenerationConfig()
        self.setWindowTitle("Video2AI Studio - 视频风格化工作台")
        self.resize(1000, 800)

        self.homeInterface = HomeInterface(self.config, self)
        self.settingInterface = SettingInterface(self.config, self)

        self.addSubInterface(self.homeInterface, FIF.HOME, "工作台")
        self.addSubInterface(self.settingInterface, FIF.SETTING, "设置")

        self._run_startup_checks()

    def _run_startup_checks(self):
        if not EnvironmentChecker.check_ffmpeg():
            InfoBar.error('环境缺失', '未检测到 FFmpeg！', parent=self)
        if not EnvironmentChecker.check_cuda():
            InfoBar.warning('GPU 不可用', '未检测到 CUDA 环境。', parent=self, duration=5000)
        else:
            InfoBar.success('GPU 就绪', f'已连接至: {EnvironmentChecker.get_cuda_info()}', parent=self)