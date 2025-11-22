import os
import cv2
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFileDialog
from qfluentwidgets import (
    SubtitleLabel, PrimaryPushButton, ProgressBar,
    InfoBar, InfoBarPosition, CardWidget, IconWidget,
    BodyLabel, FluentIcon as FIF, ScrollArea,
    PushSettingCard, LineEdit, TextEdit, CaptionLabel
)

from core.worker import AIWorker
from gui.custom_components import SimpleRangeSettingCard, SimpleSwitchSettingCard


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
        self.vBoxLayout.addWidget(SubtitleLabel("工作台", self.scrollWidget))
        self.vBoxLayout.addSpacing(10)

        # 1. 视频选择
        self.dropArea = CardWidget(self.scrollWidget)
        self.dropArea.setAcceptDrops(True)
        self.dropArea.setFixedHeight(120)
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

        # 视频信息卡片
        self.infoCard = CardWidget(self.scrollWidget)
        self.infoLayout = QHBoxLayout(self.infoCard)
        self.infoLabel = BodyLabel("等待加载视频...", self.infoCard)
        self.infoLayout.addWidget(self.infoLabel, 0, Qt.AlignmentFlag.AlignCenter)
        self.infoCard.setVisible(False)
        self.vBoxLayout.addWidget(self.infoCard)
        self.vBoxLayout.addSpacing(20)

        # 2. 预处理设置
        self.vBoxLayout.addWidget(CaptionLabel("1. 预处理设置", self.scrollWidget))

        # 骨骼开关
        self.poseSwitch = SimpleSwitchSettingCard(
            self.config.enable_pose, FIF.PEOPLE,
            "启用骨骼提取 (OpenPose)",
            "开启：完全基于骨骼重绘 (适合转动漫)。关闭：图生图模式 (保留原画面细节)。",
            self.scrollWidget
        )
        self.poseSwitch.checkedChanged.connect(self._on_pose_switch_changed)
        self.vBoxLayout.addWidget(self.poseSwitch)

        self.fpsCard = SimpleRangeSettingCard(
            self.config.target_fps, 60, FIF.SPEED_HIGH,
            "目标帧率 (FPS)", "建议 12/15/24", self.scrollWidget
        )
        self.fpsCard.valueChanged.connect(lambda v: setattr(self.config, 'target_fps', v))
        self.vBoxLayout.addWidget(self.fpsCard)

        self.widthCard = SimpleRangeSettingCard(
            self.config.target_width, 1024, FIF.ZOOM_IN,
            "目标宽度 (像素)", "默认 512", self.scrollWidget
        )
        self.widthCard.valueChanged.connect(lambda v: setattr(self.config, 'target_width', v))
        self.vBoxLayout.addWidget(self.widthCard)
        self.vBoxLayout.addSpacing(20)

        # 3. 生成参数
        self.vBoxLayout.addWidget(CaptionLabel("2. 生成参数设置", self.scrollWidget))

        self.modelCard = PushSettingCard(
            "选择模型", FIF.FOLDER,
            "Stable Diffusion 模型 (.safetensors)",
            self.config.model_path if self.config.model_path else "默认: 在线下载 runwayml/stable-diffusion-v1-5",
            self.scrollWidget
        )
        self.modelCard.clicked.connect(self.select_model)
        self.vBoxLayout.addWidget(self.modelCard)

        self.promptEdit = TextEdit(self.scrollWidget)
        self.promptEdit.setPlaceholderText("提示词 (Prompt)")
        self.promptEdit.setText(self.config.prompt)
        self.promptEdit.setFixedHeight(80)
        self.promptEdit.textChanged.connect(lambda: setattr(self.config, 'prompt', self.promptEdit.toPlainText()))
        self.vBoxLayout.addWidget(self.promptEdit)

        # 重绘幅度 (仅 Img2Img 模式显示)
        self.strengthCard = SimpleRangeSettingCard(
            int(self.config.denoising_strength * 100), 100, FIF.BRUSH,
            "重绘幅度 (Denoising Strength)", "仅在关闭骨骼时生效。数值越大变化越大 (显示值/100)。", self.scrollWidget
        )
        self.strengthCard.setVisible(False)
        self.strengthCard.valueChanged.connect(self._update_strength)
        self.vBoxLayout.addWidget(self.strengthCard)

        self.stepsCard = SimpleRangeSettingCard(
            self.config.steps, 60, FIF.SYNC,
            "迭代步数 (Steps)", "建议 20-30", self.scrollWidget
        )
        self.stepsCard.valueChanged.connect(lambda v: setattr(self.config, 'steps', v))
        self.vBoxLayout.addWidget(self.stepsCard)

        self.cfgCard = SimpleRangeSettingCard(
            int(self.config.cfg_scale * 10), 200, FIF.PALETTE,
            "提示词相关性 (CFG Scale)", "建议 7.0-9.0 (显示值/10)", self.scrollWidget
        )
        self.cfgCard.valueChanged.connect(
            lambda v: (setattr(self.config, 'cfg_scale', v / 10.0), self.cfgCard.valueLabel.setText(f"{v / 10.0:.1f}")))
        self.vBoxLayout.addWidget(self.cfgCard)

        self.seedInput = LineEdit(self.scrollWidget)
        self.seedInput.setPlaceholderText("随机种子 (Seed)")
        self.seedInput.setText(str(self.config.seed))
        self.seedInput.textChanged.connect(lambda t: setattr(self.config, 'seed', int(t)) if t.isdigit() else None)
        self.vBoxLayout.addWidget(self.seedInput)
        self.vBoxLayout.addSpacing(30)

        # 4. 控制区
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

    def _update_strength(self, value):
        self.config.denoising_strength = value / 100.0
        self.strengthCard.valueLabel.setText(f"{self.config.denoising_strength:.2f}")

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
                self.infoLabel.setText(f"源: {w}x{h} | FPS: {fps:.2f}")
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