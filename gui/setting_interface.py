from PyQt6.QtWidgets import QWidget, QVBoxLayout, QFileDialog
from qfluentwidgets import (
    SubtitleLabel, PushSettingCard, RangeSettingCard,
    SwitchSettingCard, LineEdit, TextEdit, ScrollArea,
    FluentIcon as FIF
)


class SettingInterface(ScrollArea):
    """
    设置中心：管理 AI 模型与生成参数
    """

    def __init__(self, config, parent=None):
        super().__init__(parent=parent)
        self.config = config

        self.scrollWidget = QWidget()
        self.expandLayout = QVBoxLayout(self.scrollWidget)
        self.setObjectName("settingInterface")

        self._init_ui()

    def _init_ui(self):
        # 标题
        self.expandLayout.addWidget(SubtitleLabel("生成参数设置", self.scrollWidget))
        self.expandLayout.addSpacing(10)

        # 1. 模型选择卡片
        self.modelCard = PushSettingCard(
            "选择文件",
            FIF.FOLDER,
            "Stable Diffusion 模型 (.safetensors)",
            self.config.model_path if self.config.model_path else "默认: 在线下载 runwaml/stable-diffusion-v1-5",
            self.scrollWidget
        )
        self.modelCard.clicked.connect(self.select_model)
        self.expandLayout.addWidget(self.modelCard)

        # 2. 提示词编辑框
        self.promptEdit = TextEdit(self.scrollWidget)
        self.promptEdit.setPlaceholderText("正向提示词 (Prompt)")
        self.promptEdit.setText(self.config.prompt)
        self.promptEdit.setFixedHeight(100)
        self.promptEdit.textChanged.connect(lambda: setattr(self.config, 'prompt', self.promptEdit.toPlainText()))
        self.expandLayout.addWidget(self.promptEdit)

        # 3. 步数设置滑块
        self.stepsCard = RangeSettingCard(
            self.config.steps, 60,
            FIF.SPEED_HIGH,
            "迭代步数 (Steps)",
            "ControlNet 通常需要 20-30 步。步数越高，生成越慢但细节越好。",
            self.scrollWidget
        )
        self.stepsCard.setValue(self.config.steps)
        self.stepsCard.valueChanged.connect(lambda v: setattr(self.config, 'steps', v))
        self.expandLayout.addWidget(self.stepsCard)

        # 4. CFG Scale (提示词相关性)
        self.cfgCard = RangeSettingCard(
            int(self.config.cfg_scale * 10), 200,
            FIF.PALETTE,
            "提示词相关性 (CFG Scale)",
            "数值越高越遵循提示词，建议 7.0-9.0",
            self.scrollWidget
        )
        self.cfgCard.setValue(int(self.config.cfg_scale * 10))
        # 转换逻辑：滑块(75) -> 真实值(7.5)
        self.cfgCard.valueChanged.connect(lambda v: setattr(self.config, 'cfg_scale', v / 10.0))
        self.expandLayout.addWidget(self.cfgCard)

        # 5. 随机种子输入框
        self.seedInput = LineEdit(self.scrollWidget)
        self.seedInput.setPlaceholderText("随机种子 (Seed)")
        self.seedInput.setText(str(self.config.seed))
        self.seedInput.textChanged.connect(self._update_seed)
        self.expandLayout.addWidget(self.seedInput)

        # 6. 性能开关
        self.xformersCard = SwitchSettingCard(
            FIF.FLASH,
            "启用 xFormers 内存优化",
            "显著降低显存占用并加速推理 (需要环境安装 xformers 库)",
            self.config.use_xformers,
            self.scrollWidget
        )
        self.xformersCard.checkedChanged.connect(lambda v: setattr(self.config, 'use_xformers', v))
        self.expandLayout.addWidget(self.xformersCard)

        self.expandLayout.addStretch(1)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)

    def select_model(self):
        fname, _ = QFileDialog.getOpenFileName(
            self, "选择模型", "", "Safetensors (*.safetensors);;All Files (*)"
        )
        if fname:
            self.config.model_path = fname
            self.modelCard.setContent(fname)

    def _update_seed(self, text):
        if text.isdigit():
            self.config.seed = int(text)