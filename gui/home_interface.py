import os
import cv2
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFileDialog
from qfluentwidgets import (
    SubtitleLabel, PrimaryPushButton, ProgressBar,
    InfoBar, InfoBarPosition, CardWidget, IconWidget,
    BodyLabel, FluentIcon as FIF, ScrollArea,
    PushSettingCard, TextEdit, CaptionLabel
)

from core.worker import AIWorker
from gui.custom_components import (
    SimpleSpinBoxSettingCard,
    SimpleDoubleSpinBoxSettingCard,
    SimpleSwitchSettingCard,
    SimpleLineEditSettingCard
)


class HomeInterface(ScrollArea):
    def __init__(self, config, parent=None):
        super().__init__(parent=parent)
        self.config = config
        self.scrollWidget = QWidget()
        self.vBoxLayout = QVBoxLayout(self.scrollWidget)
        self.setObjectName("homeInterface")
        self._init_ui()
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)

    def _init_ui(self):
        self.vBoxLayout.setSpacing(15)  # 设置全局垂直间距
        self.vBoxLayout.setContentsMargins(30, 20, 30, 30)  # 设置页边距

        self.vBoxLayout.addWidget(SubtitleLabel("工作台", self.scrollWidget))

        # ==================================================
        # 1. 视频选择区域
        # ==================================================
        self.dropArea = CardWidget(self.scrollWidget)
        self.dropArea.setAcceptDrops(True)
        self.dropArea.setFixedHeight(100)  # 稍微调低高度，更紧凑
        layout = QVBoxLayout(self.dropArea)
        self.iconWidget = IconWidget(FIF.VIDEO, self.dropArea)
        self.iconWidget.setFixedSize(32, 32)
        self.hintLabel = BodyLabel("拖入视频文件，或点击此处选择", self.dropArea)
        layout.addWidget(self.iconWidget, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.hintLabel, 0, Qt.AlignmentFlag.AlignHCenter)
        self.dropArea.mousePressEvent = self.selectFile
        self.dropArea.dragEnterEvent = lambda e: e.accept() if e.mimeData().hasUrls() else e.ignore()
        self.dropArea.dropEvent = self.dropEvent
        self.vBoxLayout.addWidget(self.dropArea)

        # 视频信息卡片 (默认隐藏)
        self.infoCard = CardWidget(self.scrollWidget)
        self.infoCard.setFixedHeight(50)  # 紧凑高度
        self.infoLayout = QHBoxLayout(self.infoCard)
        self.infoLayout.setContentsMargins(10, 0, 10, 0)
        self.infoLabel = BodyLabel("等待加载视频...", self.infoCard)
        self.infoLayout.addWidget(self.infoLabel, 0, Qt.AlignmentFlag.AlignCenter)
        self.infoCard.setVisible(False)
        self.vBoxLayout.addWidget(self.infoCard)

        self.vBoxLayout.addSpacing(10)

        # ==================================================
        # 2. 预处理设置 (分组布局)
        # ==================================================
        self.vBoxLayout.addWidget(CaptionLabel("1. 预处理设置", self.scrollWidget))

        # 骨骼开关 (独占一行)
        self.poseSwitch = SimpleSwitchSettingCard(
            self.config.enable_pose, FIF.PEOPLE,
            "启用骨骼提取",
            "开启：基于骨骼重绘(动漫化) | 关闭：图生图(风格迁移)",
            self.scrollWidget
        )
        self.poseSwitch.checkedChanged.connect(self._on_pose_switch_changed)
        self.vBoxLayout.addWidget(self.poseSwitch)

        # [布局优化] 目标帧率 和 目标宽度 并排显示
        prepLayout = QHBoxLayout()
        prepLayout.setSpacing(15)

        self.fpsCard = SimpleSpinBoxSettingCard(
            self.config.target_fps, 1, 60, FIF.SPEED_HIGH,
            "目标帧率 (FPS)", "建议 12/15/24", self.scrollWidget
        )
        self.fpsCard.valueChanged.connect(lambda v: setattr(self.config, 'target_fps', v))

        self.widthCard = SimpleSpinBoxSettingCard(
            self.config.target_width, 256, 2048, FIF.ZOOM_IN,
            "目标宽度 (PX)", "默认 512", self.scrollWidget
        )
        self.widthCard.valueChanged.connect(lambda v: setattr(self.config, 'target_width', v))

        prepLayout.addWidget(self.fpsCard)
        prepLayout.addWidget(self.widthCard)
        self.vBoxLayout.addLayout(prepLayout)

        self.vBoxLayout.addSpacing(10)

        # ==================================================
        # 3. 生成参数设置 (分组布局)
        # ==================================================
        self.vBoxLayout.addWidget(CaptionLabel("2. 生成参数设置", self.scrollWidget))

        # 模型选择
        self.modelCard = PushSettingCard(
            "选择文件", FIF.FOLDER,
            "基础模型 (Checkpoint)",
            self.config.model_path if self.config.model_path else "仅支持safetensor类型",
            self.scrollWidget
        )
        self.modelCard.clicked.connect(self.select_model)
        self.vBoxLayout.addWidget(self.modelCard)

        # 提示词
        self.promptEdit = TextEdit(self.scrollWidget)
        self.promptEdit.setPlaceholderText("提示词 (Prompt) - 例如: anime style, masterpiece, best quality")
        self.promptEdit.setText(self.config.prompt)
        self.promptEdit.setFixedHeight(70)  # 稍微减小高度
        self.promptEdit.textChanged.connect(lambda: setattr(self.config, 'prompt', self.promptEdit.toPlainText()))
        self.vBoxLayout.addWidget(self.promptEdit)

        # 重绘幅度 (条件显示)
        self.strengthCard = SimpleDoubleSpinBoxSettingCard(
            self.config.denoising_strength, 0.0, 1.0, 0.05, FIF.BRUSH,
            "重绘幅度", "关闭骨骼时生效，数值越大变化越大", self.scrollWidget
        )
        self.strengthCard.setVisible(False)
        self.strengthCard.valueChanged.connect(lambda v: setattr(self.config, 'denoising_strength', v))
        self.vBoxLayout.addWidget(self.strengthCard)

        # [布局优化] 步数 和 CFG Scale 并排显示
        genLayout = QHBoxLayout()
        genLayout.setSpacing(15)

        self.stepsCard = SimpleSpinBoxSettingCard(
            self.config.steps, 1, 100, FIF.SYNC,
            "迭代步数", "建议 20-30", self.scrollWidget
        )
        self.stepsCard.valueChanged.connect(lambda v: setattr(self.config, 'steps', v))

        self.cfgCard = SimpleDoubleSpinBoxSettingCard(
            self.config.cfg_scale, 1.0, 30.0, 0.5, FIF.PALETTE,
            "CFG Scale", "建议 7.0-9.0", self.scrollWidget
        )
        self.cfgCard.valueChanged.connect(lambda v: setattr(self.config, 'cfg_scale', v))

        genLayout.addWidget(self.stepsCard)
        genLayout.addWidget(self.cfgCard)
        self.vBoxLayout.addLayout(genLayout)

        # 种子 (独占一行)
        self.seedCard = SimpleLineEditSettingCard(
            str(self.config.seed), "随机种子", FIF.EDIT,
            "随机种子 (Seed)", "固定种子以减少画面闪烁", self.scrollWidget
        )
        self.seedCard.textChanged.connect(lambda t: setattr(self.config, 'seed', int(t)) if t.isdigit() else None)
        self.vBoxLayout.addWidget(self.seedCard)

        self.vBoxLayout.addSpacing(20)

        # ==================================================
        # 4. 控制区
        # ==================================================
        self.progressBar = ProgressBar(self.scrollWidget)
        self.statusLabel = BodyLabel("准备就绪", self.scrollWidget)
        self.statusLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.startBtn = PrimaryPushButton("开始生成处理", self.scrollWidget)
        self.startBtn.clicked.connect(self.start_processing)

        self.vBoxLayout.addWidget(self.statusLabel)
        self.vBoxLayout.addWidget(self.progressBar)
        self.vBoxLayout.addWidget(self.startBtn)
        self.vBoxLayout.addStretch(1)

    def _on_pose_switch_changed(self, is_checked):
        self.config.enable_pose = is_checked
        self.strengthCard.setVisible(not is_checked)

    def dropEvent(self, e):
        files = [u.toLocalFile() for u in e.mimeData().urls()]
        if files: self.load_video(files[0])

    def selectFile(self, e):
        fname, _ = QFileDialog.getOpenFileName(self, "选择视频", "", "Video Files (*.mp4 *.avi *.mov)")
        if fname: self.load_video(fname)

    def select_model(self):
        fname, _ = QFileDialog.getOpenFileName(self, "选择模型", "", "Safetensors (*.safetensors);;All Files (*)")
        if fname: self.modelCard.setContent(fname); self.config.model_path = fname

    def load_video(self, path):
        self.config.input_video_path = path
        self.hintLabel.setText(f"已选择: {os.path.basename(path)}")
        self.iconWidget.setIcon(FIF.COMPLETED)
        try:
            cap = cv2.VideoCapture(path)
            if cap.isOpened():
                w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = cap.get(cv2.CAP_PROP_FPS)
                self.infoLabel.setText(f"源信息: {w}x{h} | FPS: {fps:.2f}")
                self.infoCard.setVisible(True)
                self.config.target_width = w if w < 512 else 512
                self.widthCard.setValue(self.config.target_width)
                self.config.target_fps = int(fps) if fps < 24 else 24
                self.fpsCard.setValue(self.config.target_fps)
            cap.release()
        except Exception:
            pass

    def start_processing(self):
        if not self.config.input_video_path: return
        self.startBtn.setEnabled(False)
        self.startBtn.setText("处理中...")
        self.worker = AIWorker(self.config)
        self.worker.progress_signal.connect(lambda v, t: (self.progressBar.setValue(v), self.statusLabel.setText(t)))
        self.worker.finished_signal.connect(
            lambda: (self.startBtn.setEnabled(True), self.startBtn.setText("开始"), self.progressBar.setValue(100),
                     self._msg("完成", "处理结束", False)))
        self.worker.error_signal.connect(
            lambda e: (self.startBtn.setEnabled(True), self.statusLabel.setText("错误"), self._msg("失败", e, True)))
        self.worker.start()

    def _msg(self, title, content, is_error):
        func = InfoBar.error if is_error else InfoBar.success
        func(title=title, content=content, parent=self, position=InfoBarPosition.TOP, duration=3000)