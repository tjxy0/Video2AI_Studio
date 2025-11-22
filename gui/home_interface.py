import os
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QFileDialog
from qfluentwidgets import (
    SubtitleLabel, PrimaryPushButton, ProgressBar,
    InfoBar, InfoBarPosition, CardWidget, IconWidget,
    BodyLabel, FluentIcon as FIF
)

from core.worker import AIWorker


class HomeInterface(QWidget):
    """
    主工作台：负责文件摄取与任务启动
    """

    def __init__(self, config, parent=None):
        super().__init__(parent=parent)
        self.config = config
        self.worker = None

        self._init_ui()

    def _init_ui(self):
        self.setObjectName("homeInterface")
        self.vBoxLayout = QVBoxLayout(self)

        # 1. 标题
        self.titleLabel = SubtitleLabel("视频风格化工作台", self)

        # 2. 拖拽区域
        self.dropArea = CardWidget(self)
        self.dropArea.setAcceptDrops(True)
        self.dropArea.setFixedSize(600, 200)
        self.dropAreaLayout = QVBoxLayout(self.dropArea)

        self.iconWidget = IconWidget(FIF.VIDEO, self.dropArea)
        self.iconWidget.setFixedSize(48, 48)
        self.hintLabel = BodyLabel("将视频文件拖拽至此，或点击选择", self.dropArea)

        self.dropAreaLayout.addWidget(self.iconWidget, 0, Qt.AlignmentFlag.AlignHCenter)
        self.dropAreaLayout.addWidget(self.hintLabel, 0, Qt.AlignmentFlag.AlignHCenter)

        # 绑定事件
        self.dropArea.dragEnterEvent = self.dragEnterEvent
        self.dropArea.dropEvent = self.dropEvent
        self.dropArea.mousePressEvent = self.selectFile

        # 3. 进度显示
        self.progressBar = ProgressBar(self)
        self.progressBar.setFixedWidth(600)
        self.progressBar.setValue(0)
        self.statusLabel = BodyLabel("准备就绪", self)

        # 4. 控制按钮
        self.startBtn = PrimaryPushButton("开始生成处理", self)
        self.startBtn.setFixedWidth(200)
        self.startBtn.clicked.connect(self.start_processing)

        # 布局组装
        self.vBoxLayout.addStretch(1)
        self.vBoxLayout.addWidget(self.titleLabel, 0, Qt.AlignmentFlag.AlignHCenter)
        self.vBoxLayout.addSpacing(20)
        self.vBoxLayout.addWidget(self.dropArea, 0, Qt.AlignmentFlag.AlignHCenter)
        self.vBoxLayout.addSpacing(30)
        self.vBoxLayout.addWidget(self.statusLabel, 0, Qt.AlignmentFlag.AlignHCenter)
        self.vBoxLayout.addWidget(self.progressBar, 0, Qt.AlignmentFlag.AlignHCenter)
        self.vBoxLayout.addSpacing(20)
        self.vBoxLayout.addWidget(self.startBtn, 0, Qt.AlignmentFlag.AlignHCenter)
        self.vBoxLayout.addStretch(1)

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, e):
        files = [u.toLocalFile() for u in e.mimeData().urls()]
        if files:
            self.load_video(files[0])

    def selectFile(self, e):
        fname, _ = QFileDialog.getOpenFileName(self, "选择视频", "", "Video Files (*.mp4 *.avi *.mov)")
        if fname:
            self.load_video(fname)

    def load_video(self, path):
        self.config.input_video_path = path
        self.hintLabel.setText(f"已加载: {os.path.basename(path)}")
        self.iconWidget.setIcon(FIF.COMPLETED)

    def start_processing(self):
        if not self.config.input_video_path:
            self._show_message("未选择视频", "请先拖入或选择一个视频文件。", is_error=True)
            return

        # 锁定 UI
        self.startBtn.setEnabled(False)
        self.startBtn.setText("处理中...")
        self.progressBar.setValue(0)

        # 启动 Worker
        self.worker = AIWorker(self.config)
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.finished_signal.connect(self.on_finished)
        self.worker.error_signal.connect(self.on_error)
        self.worker.start()

    def update_progress(self, value, text):
        self.progressBar.setValue(value)
        self.statusLabel.setText(text)

    def on_finished(self):
        self.startBtn.setEnabled(True)
        self.startBtn.setText("开始生成处理")
        self.progressBar.setValue(100)
        self._show_message("任务完成", "视频生成已完成，请查看 output 文件夹。", is_error=False)

    def on_error(self, err_msg):
        self.startBtn.setEnabled(True)
        self.startBtn.setText("开始生成处理")
        self.statusLabel.setText("发生错误")
        self._show_message("处理失败", err_msg, is_error=True)

    def _show_message(self, title, content, is_error=False):
        func = InfoBar.error if is_error else InfoBar.success
        func(
            title=title,
            content=content,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self
        )