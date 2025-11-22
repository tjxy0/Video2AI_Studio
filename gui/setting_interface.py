from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from qfluentwidgets import SubtitleLabel, ScrollArea, FluentIcon as FIF
from gui.custom_components import SimpleSwitchSettingCard


class SettingInterface(ScrollArea):
    def __init__(self, config, parent=None):
        super().__init__(parent=parent)
        self.config = config
        self.scrollWidget = QWidget()
        self.expandLayout = QVBoxLayout(self.scrollWidget)
        self.setObjectName("settingInterface")

        self.expandLayout.addWidget(SubtitleLabel("系统与性能设置", self.scrollWidget))
        self.expandLayout.addSpacing(20)

        self.xformersCard = SimpleSwitchSettingCard(
            self.config.use_xformers, FIF.SPEED_HIGH, "启用 xFormers 内存优化",
            "需环境支持。降低显存占用，加速推理。", self.scrollWidget
        )
        self.xformersCard.checkedChanged.connect(lambda v: setattr(self.config, 'use_xformers', v))
        self.expandLayout.addWidget(self.xformersCard)

        self.lowVramCard = SimpleSwitchSettingCard(
            self.config.low_vram, FIF.ZZZ, "低显存模式 (Low VRAM)",
            "自动卸载模型至 CPU。适合 4GB-6GB 显卡。", self.scrollWidget
        )
        self.lowVramCard.checkedChanged.connect(lambda v: setattr(self.config, 'low_vram', v))
        self.expandLayout.addWidget(self.lowVramCard)

        self.expandLayout.addSpacing(20)
        self.expandLayout.addWidget(QLabel("注：以上设置将在下一次任务开始时生效。", self.scrollWidget))
        self.expandLayout.addStretch(1)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)