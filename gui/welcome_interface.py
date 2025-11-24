from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from qfluentwidgets import (
    SubtitleLabel, PrimaryPushButton, BodyLabel,
    FluentIcon as FIF, CardWidget, IconWidget
)


class WelcomeInterface(QWidget):
    """
    欢迎页面 (流程的第一步)
    """
    startClicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.vBoxLayout = QVBoxLayout(self)
        self.setObjectName("welcomeInterface")
        self._init_ui()

    def _init_ui(self):
        self.vBoxLayout.setContentsMargins(50, 50, 50, 50)
        self.vBoxLayout.setSpacing(30)
        self.vBoxLayout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 头部标题
        title_label = SubtitleLabel("欢迎使用 Video2AI Studio", self)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.vBoxLayout.addWidget(title_label)

        # 简介卡片
        intro_card = CardWidget(self)
        intro_layout = QVBoxLayout(intro_card)
        intro_layout.setContentsMargins(30, 30, 30, 30)

        # 图标和描述
        icon_label = IconWidget(FIF.VIDEO, intro_card)
        icon_label.setFixedSize(64, 64)
        icon_label.setStyleSheet("color: #0078D4;")  # Fluent Blue
        intro_layout.addWidget(icon_label, 0, Qt.AlignmentFlag.AlignCenter)

        desc_text = (
            "本工具将指导您完成视频风格化处理的全部流程：\n"
            "1. 预处理：选择视频并设置帧率/尺寸。\n"
            "2. 生成参数：配置模型、提示词和迭代步数。\n"
            "3. 任务控制：设置输出目录并启动AI工作线程。"
        )
        desc_label = BodyLabel(desc_text, intro_card)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        intro_layout.addWidget(desc_label)

        self.vBoxLayout.addWidget(intro_card)

        # 启动按钮
        self.startBtn = PrimaryPushButton(FIF.ACCEPT, "开始工作流")
        self.startBtn.setMinimumHeight(50)
        self.startBtn.clicked.connect(self.startClicked.emit)
        self.vBoxLayout.addWidget(self.startBtn, 0, Qt.AlignmentFlag.AlignHCenter)

        self.vBoxLayout.addStretch(1)