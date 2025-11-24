import os
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFileDialog
from qfluentwidgets import (
    SubtitleLabel, PrimaryPushButton, PushButton,
    BodyLabel, FluentIcon as FIF, ScrollArea,
    PushSettingCard, TextEdit, CaptionLabel
)
from gui.custom_components import (
    SimpleSpinBoxSettingCard,
    SimpleDoubleSpinBoxSettingCard,
    SimpleLineEditSettingCard
)


class Step2Interface(ScrollArea):
    """
    工作流步骤 2: 生成参数设置 (原 HomeInterface 的第 3 部分)
    """
    nextClicked = pyqtSignal()
    prevClicked = pyqtSignal()

    def __init__(self, config, parent=None):
        super().__init__(parent=parent)
        self.config = config
        self.scrollWidget = QWidget()
        self.vBoxLayout = QVBoxLayout(self.scrollWidget)
        self.setObjectName("step2Interface")
        self._init_ui()
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)

        # 初始设置重绘幅度卡的可见性
        self._on_pose_switch_changed(self.config.enable_pose)

    def _init_ui(self):
        self.vBoxLayout.setSpacing(15)
        self.vBoxLayout.setContentsMargins(30, 20, 30, 30)

        self.vBoxLayout.addWidget(SubtitleLabel("步骤 2: 生成参数设置", self.scrollWidget))

        # ==================================================
        # 1. 模型选择
        # ==================================================
        self.modelCard = PushSettingCard(
            "选择文件", FIF.FOLDER,
            "基础模型 (Checkpoint)",
            self.config.model_path if self.config.model_path else "仅支持safetensors",
            self.scrollWidget
        )
        self.modelCard.clicked.connect(self.select_model)
        self.vBoxLayout.addWidget(self.modelCard)

        self.vBoxLayout.addSpacing(5)

        # ==================================================
        # 2. 提示词设置
        # ==================================================
        self.vBoxLayout.addWidget(BodyLabel("正向提示词 (Prompt) - 描述画面内容，越详细越好", self.scrollWidget))
        self.promptEdit = TextEdit(self.scrollWidget)
        self.promptEdit.setPlaceholderText("例如: anime style, masterpiece, best quality, smiling")
        self.promptEdit.setText(self.config.prompt)
        self.promptEdit.setFixedHeight(70)
        self.promptEdit.textChanged.connect(lambda: setattr(self.config, 'prompt', self.promptEdit.toPlainText()))
        self.vBoxLayout.addWidget(self.promptEdit)

        self.vBoxLayout.addSpacing(5)

        self.vBoxLayout.addWidget(BodyLabel("负面提示词 (Negative Prompt) - 描述你不希望出现的元素", self.scrollWidget))
        self.negativePromptEdit = TextEdit(self.scrollWidget)
        self.negativePromptEdit.setPlaceholderText(
            "例如: low quality, bad anatomy, watermark, text, error, ugly, deformed")
        self.negativePromptEdit.setText(self.config.negative_prompt)
        self.negativePromptEdit.setFixedHeight(70)
        self.negativePromptEdit.textChanged.connect(
            lambda: setattr(self.config, 'negative_prompt', self.negativePromptEdit.toPlainText()))
        self.vBoxLayout.addWidget(self.negativePromptEdit)

        self.vBoxLayout.addSpacing(10)

        # ==================================================
        # 3. 核心参数
        # ==================================================

        # 重绘幅度 (条件显示)
        self.strengthCard = SimpleDoubleSpinBoxSettingCard(
            self.config.denoising_strength, 0.0, 1.0, 0.05, FIF.BRUSH,
            "重绘幅度", "关闭骨骼时生效，数值越大变化越大", self.scrollWidget
        )
        self.strengthCard.valueChanged.connect(lambda v: setattr(self.config, 'denoising_strength', v))
        self.vBoxLayout.addWidget(self.strengthCard)

        # 步数 和 CFG Scale
        genLayout = QHBoxLayout()
        genLayout.setSpacing(15)

        self.stepsCard = SimpleSpinBoxSettingCard(
            self.config.steps, 1, 100, FIF.SYNC,
            "迭代步数", "建议 20-30", self.scrollWidget
        )
        self.stepsCard.valueChanged.connect(lambda v: setattr(self.config, 'steps', v))

        self.cfgCard = SimpleDoubleSpinBoxSettingCard(
            self.config.cfg_scale, 1.0, 30.0, 0.5, FIF.PALETTE,
            "CFG Scale", "提示词引导系数", self.scrollWidget
        )
        self.cfgCard.valueChanged.connect(lambda v: setattr(self.config, 'cfg_scale', v))

        genLayout.addWidget(self.stepsCard)
        genLayout.addWidget(self.cfgCard)
        self.vBoxLayout.addLayout(genLayout)

        # 种子
        self.seedCard = SimpleLineEditSettingCard(
            str(self.config.seed), "随机种子", FIF.EDIT,
            "随机种子 (Seed)", "固定种子以减少画面闪烁", self.scrollWidget
        )
        self.seedCard.textChanged.connect(
            lambda t: setattr(self.config, 'seed', int(t)) if t.isdigit() and t else setattr(self.config, 'seed', 12345)
        )
        self.vBoxLayout.addWidget(self.seedCard)

        self.vBoxLayout.addStretch(1)

        # ==================================================
        # 4. 底部导航
        # ==================================================
        navLayout = QHBoxLayout()
        self.prevBtn = PushButton("上一步", self.scrollWidget)
        self.prevBtn.clicked.connect(self.prevClicked.emit)

        self.nextBtn = PrimaryPushButton("下一步", self.scrollWidget)
        self.nextBtn.clicked.connect(self.nextClicked.emit)

        navLayout.addWidget(self.prevBtn)
        navLayout.addStretch(1)
        navLayout.addWidget(self.nextBtn)

        self.vBoxLayout.addLayout(navLayout)

    # --------------------------------------------------
    # 逻辑部分
    # --------------------------------------------------
    def select_model(self):
        """选择模型文件"""
        fname, _ = QFileDialog.getOpenFileName(self, "选择模型", "", "Safetensors (*.safetensors);;All Files (*)")
        if fname:
            self.modelCard.setContent(fname)
            self.config.model_path = fname

    def _on_pose_switch_changed(self, is_checked):
        """根据骨骼开关状态更新重绘幅度卡的可见性"""
        self.strengthCard.setVisible(not is_checked)