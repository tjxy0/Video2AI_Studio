from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from qfluentwidgets import SubtitleLabel, ScrollArea, FluentIcon as FIF, SettingCard, PrimaryPushSettingCard
from gui.custom_components import SimpleSwitchSettingCard
from core.env_checker import EnvironmentChecker


class SettingInterface(ScrollArea):
    def __init__(self, config, parent=None):
        super().__init__(parent=parent)
        self.config = config
        self.scrollWidget = QWidget()
        self.expandLayout = QVBoxLayout(self.scrollWidget)
        self.setObjectName("settingInterface")

        self._init_ui()

    def _init_ui(self):
        self.expandLayout.setContentsMargins(30, 20, 30, 30)
        self.expandLayout.setSpacing(15)

        # ==================================================
        # 1. 环境状态检测 (新增)
        # ==================================================
        self.expandLayout.addWidget(SubtitleLabel("当前环境状态", self.scrollWidget))

        # 检查各项环境
        cuda_info = EnvironmentChecker.get_cuda_info()
        has_ffmpeg = EnvironmentChecker.check_ffmpeg()
        has_xformers = EnvironmentChecker.check_xformers()

        # GPU 信息卡片
        self.gpuCard = SettingCard(
            FIF.VIDEO, "GPU (CUDA)",
            cuda_info if cuda_info != "N/A" else "未检测到 CUDA 设备",
            self.scrollWidget
        )
        self.expandLayout.addWidget(self.gpuCard)

        # 依赖库状态卡片
        status_text = f"FFmpeg: {'已安装' if has_ffmpeg else '未找到'} | xFormers: {'已安装' if has_xformers else '未找到'}"
        self.envCard = SettingCard(
            FIF.DEVELOPER_TOOLS, "核心组件状态",
            status_text,
            self.scrollWidget
        )
        self.expandLayout.addWidget(self.envCard)

        self.expandLayout.addSpacing(20)

        # ==================================================
        # 2. 系统与性能设置
        # ==================================================
        self.expandLayout.addWidget(SubtitleLabel("系统与性能设置", self.scrollWidget))

        # --- xFormers 开关 (动态检测) ---
        xformers_desc = "显著降低显存占用并加速推理。"

        # 如果未检测到 xFormers
        if not has_xformers:
            xformers_desc += " [当前环境未检测到 xformers 库，选项已禁用]"
            # 强制关闭配置，防止误开启
            self.config.use_xformers = False

        self.xformersCard = SimpleSwitchSettingCard(
            self.config.use_xformers, FIF.SPEED_HIGH, "启用 xFormers 内存优化",
            xformers_desc, self.scrollWidget
        )

        # 关键修改：如果没有 xformers，直接让整个卡片变灰不可点
        if not has_xformers:
            self.xformersCard.setEnabled(False)
            # 确保开关也是关闭状态
            self.xformersCard.switchButton.setChecked(False)

        self.xformersCard.checkedChanged.connect(lambda v: setattr(self.config, 'use_xformers', v))
        self.expandLayout.addWidget(self.xformersCard)

        # --- Low VRAM 开关 ---
        self.lowVramCard = SimpleSwitchSettingCard(
            self.config.low_vram, FIF.TILES, "低显存模式 (Low VRAM)",
            "自动卸载模型至 CPU。适合 4GB-6GB 显卡。", self.scrollWidget
        )
        self.lowVramCard.checkedChanged.connect(lambda v: setattr(self.config, 'low_vram', v))
        self.expandLayout.addWidget(self.lowVramCard)

        self.expandLayout.addSpacing(20)
        self.expandLayout.addWidget(QLabel("注：以上设置将在下一次任务开始时生效。", self.scrollWidget))
        self.expandLayout.addStretch(1)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)