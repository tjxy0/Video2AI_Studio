import os
import cv2
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFileDialog
from qfluentwidgets import (
    SubtitleLabel, PrimaryPushButton, PushButton, ProgressBar,
    InfoBar, InfoBarPosition, CardWidget, IconWidget,
    BodyLabel, FluentIcon as FIF, ScrollArea,
    PushSettingCard, TextEdit, CaptionLabel
)

# 保留导入，用于初始化组件
from core.worker import AIWorker
from gui.custom_components import (
    SimpleSpinBoxSettingCard,
    SimpleDoubleSpinBoxSettingCard,
    SimpleSwitchSettingCard,
    SimpleLineEditSettingCard
)


# 将 HomeInterface 重命名为 Step1Interface
class Step1Interface(ScrollArea):
    """
    工作流步骤 1: 视频选择与预处理设置 (原 HomeInterface 的前两部分)
    """
    nextClicked = pyqtSignal()

    def __init__(self, config, parent=None):
        super().__init__(parent=parent)
        self.config = config
        self.scrollWidget = QWidget()
        self.vBoxLayout = QVBoxLayout(self.scrollWidget)
        self.setObjectName("step1Interface")
        self._init_ui()
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)

    def _init_ui(self):
        self.vBoxLayout.setSpacing(15)  # 设置全局垂直间距
        self.vBoxLayout.setContentsMargins(30, 20, 30, 30)  # 设置页边距

        self.vBoxLayout.addWidget(SubtitleLabel("步骤 1: 视频与预处理设置", self.scrollWidget))

        # ==================================================
        # 1. 视频选择区域 (保持不变)
        # ==================================================
        self.dropArea = CardWidget(self.scrollWidget)
        self.dropArea.setAcceptDrops(True)
        self.dropArea.setFixedHeight(100)
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

        # 视频信息卡片 (保持不变)
        self.infoCard = CardWidget(self.scrollWidget)
        self.infoCard.setFixedHeight(50)
        self.infoLayout = QHBoxLayout(self.infoCard)
        self.infoLayout.setContentsMargins(10, 0, 10, 0)
        self.infoLabel = BodyLabel("等待加载视频...", self.infoCard)
        self.infoLayout.addWidget(self.infoLabel, 0, Qt.AlignmentFlag.AlignCenter)
        self.infoCard.setVisible(False)
        self.vBoxLayout.addWidget(self.infoCard)

        self.vBoxLayout.addSpacing(10)

        # ==================================================
        # 2. 预处理设置 (保持不变)
        # ==================================================
        self.vBoxLayout.addWidget(CaptionLabel("预处理设置", self.scrollWidget))

        # 骨骼开关
        self.poseSwitch = SimpleSwitchSettingCard(
            self.config.enable_pose, FIF.PEOPLE,
            "启用骨骼提取",
            "开启：基于骨骼重绘(动漫化) | 关闭：图生图(风格迁移)",
            self.scrollWidget
        )
        # 注意：这里需要连接信号，以便同步到 Step2 的重绘幅度卡片
        self.poseSwitch.checkedChanged.connect(lambda v: setattr(self.config, 'enable_pose', v))
        self.vBoxLayout.addWidget(self.poseSwitch)

        # 目标帧率 和 目标宽度
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

        self.vBoxLayout.addStretch(1)

        # ==================================================
        # 3. 底部导航 (新增)
        # ==================================================
        navLayout = QHBoxLayout()
        navLayout.addStretch(1)

        # 视频检查标签
        self.videoCheckLabel = BodyLabel("请先选择视频文件", self.scrollWidget)
        self.videoCheckLabel.setStyleSheet("color: red;")
        navLayout.addWidget(self.videoCheckLabel)

        navLayout.addSpacing(20)

        self.nextBtn = PrimaryPushButton("下一步", self.scrollWidget)
        self.nextBtn.setEnabled(False)  # 默认禁用，直到选择视频
        self.nextBtn.clicked.connect(self.check_video_and_emit)
        navLayout.addWidget(self.nextBtn)

        self.vBoxLayout.addLayout(navLayout)

    # --------------------------------------------------
    # 逻辑部分 (保留和修改)
    # --------------------------------------------------
    def check_video_and_emit(self):
        """检查视频路径，如果有效则发射 nextClicked 信号"""
        if self.config.input_video_path and os.path.exists(self.config.input_video_path):
            self.nextClicked.emit()
        else:
            # 使用 InfoBar 给出更友好的提示
            self._msg("提示", "请先选择一个有效的视频文件！", True)

    def dropEvent(self, e):
        files = [u.toLocalFile() for u in e.mimeData().urls()]
        if files: self.load_video(files[0])

    def selectFile(self, e):
        fname, _ = QFileDialog.getOpenFileName(self, "选择视频", "", "Video Files (*.mp4 *.avi *.mov)")
        if fname: self.load_video(fname)

    def load_video(self, path):
        self.config.input_video_path = path
        self.hintLabel.setText(f"已选择: {os.path.basename(path)}")
        self.iconWidget.setIcon(FIF.COMPLETED)

        # 激活下一步按钮
        self.nextBtn.setEnabled(True)
        self.videoCheckLabel.setText("视频已加载")
        self.videoCheckLabel.setStyleSheet("color: green;")

        try:
            cap = cv2.VideoCapture(path)
            if cap.isOpened():
                w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = cap.get(cv2.CAP_PROP_FPS)
                self.infoLabel.setText(f"源信息: {w}x{h} | FPS: {fps:.2f}")
                self.infoCard.setVisible(True)

                # 调整目标尺寸和帧率
                self.config.target_width = w if w < 512 else 512
                self.widthCard.setValue(self.config.target_width)
                self.config.target_fps = int(fps) if fps < 24 else 24
                self.fpsCard.setValue(self.config.target_fps)

            cap.release()
        except Exception:
            pass

    def _msg(self, title, content, is_error):
        # 简化 InfoBar 调用，确保其在父窗口显示
        func = InfoBar.error if is_error else InfoBar.success
        func(title=title, content=content, parent=self, position=InfoBarPosition.TOP, duration=3000)