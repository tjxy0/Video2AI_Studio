from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from qfluentwidgets import SubtitleLabel, ScrollArea, FluentIcon as FIF
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
        self.expandLayout.addWidget(SubtitleLabel("系统与性能设置", self.scrollWidget))
        self.expandLayout.addSpacing(20)

        # --- xFormers 开关 (动态检测) ---
        has_xformers = EnvironmentChecker.check_xformers()
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