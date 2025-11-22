from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFileDialog
from qfluentwidgets import (
    SubtitleLabel, PushSettingCard, SettingCard,
    SwitchButton, Slider, LineEdit, TextEdit, ScrollArea,
    FluentIcon as FIF
)


class SimpleRangeSettingCard(SettingCard):
    """
    自定义的范围设置卡片，不依赖 ConfigItem，直接处理数值。
    包含：图标、标题、内容、滑块、数值显示标签
    """
    valueChanged = pyqtSignal(int)

    def __init__(self, value, max_value, icon, title, content=None, parent=None):
        super().__init__(icon, title, content, parent)

        # 创建滑块
        self.slider = Slider(Qt.Orientation.Horizontal, self)
        self.slider.setRange(1, max_value)
        self.slider.setValue(value)
        self.slider.setFixedWidth(150)

        # 创建数值显示标签
        self.valueLabel = QLabel(str(value), self)
        self.valueLabel.setFixedWidth(30)
        self.valueLabel.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        # 将组件添加到卡片右侧布局中
        self.hBoxLayout.addWidget(self.valueLabel, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(10)
        self.hBoxLayout.addWidget(self.slider, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)

        # 信号连接
        self.slider.valueChanged.connect(self.__onValueChanged)

    def __onValueChanged(self, value):
        self.valueLabel.setText(str(value))
        self.valueChanged.emit(value)

    def setValue(self, value):
        self.slider.setValue(value)
        self.valueLabel.setText(str(value))


class SimpleSwitchSettingCard(SettingCard):
    """
    自定义的开关设置卡片，不依赖 ConfigItem。
    """
    checkedChanged = pyqtSignal(bool)

    def __init__(self, is_checked, icon, title, content=None, parent=None):
        super().__init__(icon, title, content, parent)

        self.switchButton = SwitchButton(self)
        self.switchButton.setChecked(is_checked)

        # 示例文本 (开/关)
        self.stateLabel = QLabel("开启" if is_checked else "关闭", self)
        self.stateLabel.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.hBoxLayout.addWidget(self.stateLabel, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(10)
        self.hBoxLayout.addWidget(self.switchButton, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)

        self.switchButton.checkedChanged.connect(self.__onCheckedChanged)

    def __onCheckedChanged(self, is_checked):
        self.stateLabel.setText("开启" if is_checked else "关闭")
        self.checkedChanged.emit(is_checked)


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

        # 1. 模型选择卡片 (PushSettingCard 参数通常比较稳定，直接使用)
        self.modelCard = PushSettingCard(
            "选择文件",
            FIF.FOLDER,
            "Stable Diffusion 模型 (.safetensors)",
            self.config.model_path if self.config.model_path else "默认: 在线下载 runwayml/stable-diffusion-v1-5",
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

        # 3. 步数设置滑块 (使用自定义 SimpleRangeSettingCard)
        self.stepsCard = SimpleRangeSettingCard(
            self.config.steps,
            60,  # 最大值
            FIF.SPEED_HIGH,
            "迭代步数 (Steps)",
            "ControlNet 通常需要 20-30 步。步数越高，生成越慢但细节越好。",
            self.scrollWidget
        )
        self.stepsCard.valueChanged.connect(lambda v: setattr(self.config, 'steps', v))
        self.expandLayout.addWidget(self.stepsCard)

        # 4. CFG Scale (提示词相关性)
        # 我们将 CFG Scale (float) 映射为 整数 (x10) 处理
        self.cfgCard = SimpleRangeSettingCard(
            int(self.config.cfg_scale * 10),
            200,  # 最大值 20.0
            FIF.PALETTE,
            "提示词相关性 (CFG Scale)",
            "数值越高越遵循提示词，建议 7.0-9.0 (显示值需除以10)",
            self.scrollWidget
        )
        # 转换逻辑：滑块(75) -> 真实值(7.5)
        self.cfgCard.valueChanged.connect(self._update_cfg)
        self.expandLayout.addWidget(self.cfgCard)

        # 5. 随机种子输入框
        self.seedInput = LineEdit(self.scrollWidget)
        self.seedInput.setPlaceholderText("随机种子 (Seed)")
        self.seedInput.setText(str(self.config.seed))
        self.seedInput.textChanged.connect(self._update_seed)
        self.expandLayout.addWidget(self.seedInput)

        # 6. 性能开关 (使用自定义 SimpleSwitchSettingCard)
        self.xformersCard = SimpleSwitchSettingCard(
            self.config.use_xformers,
            FIF.FLASH,
            "启用 xFormers 内存优化",
            "显著降低显存占用并加速推理 (需要环境安装 xformers 库)",
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

    def _update_cfg(self, value):
        # 更新配置
        self.config.cfg_scale = value / 10.0
        # 更新标签文本以显示浮点数 (覆盖 SimpleRangeSettingCard 默认的整数显示)
        self.cfgCard.valueLabel.setText(f"{self.config.cfg_scale:.1f}")