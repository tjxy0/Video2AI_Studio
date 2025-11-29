import os
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFileDialog
from qfluentwidgets import (
    SubtitleLabel, PrimaryPushButton, PushButton, ProgressBar,
    InfoBar, InfoBarPosition, BodyLabel, FluentIcon as FIF,
    ScrollArea, PushSettingCard
)

from core.worker import AIWorker


class Step3Interface(ScrollArea):
    """
    工作流步骤 3: 输出设置与任务控制 (原 HomeInterface 的第 4/5 部分)
    """
    prevClicked = pyqtSignal()
    # 新增信号：用于通知工作流容器重置到欢迎页
    resetWorkflow = pyqtSignal()

    def __init__(self, config, parent=None):
        super().__init__(parent=parent)
        self.config = config
        self.scrollWidget = QWidget()
        self.vBoxLayout = QVBoxLayout(self.scrollWidget)
        self.setObjectName("step3Interface")
        self._init_ui()
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)

        # 保持 worker 的引用，防止被垃圾回收
        self.worker = None

    def _init_ui(self):
        self.vBoxLayout.setSpacing(15)
        self.vBoxLayout.setContentsMargins(30, 20, 30, 30)

        self.vBoxLayout.addWidget(SubtitleLabel("步骤 3: 输出设置与任务控制", self.scrollWidget))

        # ==================================================
        # 1. 输出设置
        # ==================================================
        # 输出目录选择
        self.outputDirCard = PushSettingCard(
            "选择目录", FIF.FOLDER,
            "最终输出目录",
            f"当前: {os.path.abspath(self.config.output_dir)}",
            self.scrollWidget
        )
        self.outputDirCard.clicked.connect(self.select_output_dir)
        self.vBoxLayout.addWidget(self.outputDirCard)

        self.vBoxLayout.addSpacing(20)

        # ==================================================
        # 2. 控制区
        # ==================================================
        self.progressBar = ProgressBar(self.scrollWidget)
        self.statusLabel = BodyLabel("准备就绪", self.scrollWidget)
        self.statusLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 按钮布局 (水平排列)
        buttonLayout = QHBoxLayout()
        buttonLayout.setSpacing(20)

        self.startBtn = PrimaryPushButton("开始生成处理", self.scrollWidget)
        self.startBtn.clicked.connect(self.start_processing)

        self.stopBtn = PushButton("停止任务", self.scrollWidget)
        self.stopBtn.setEnabled(False)  # 默认不可用
        self.stopBtn.clicked.connect(self.stop_processing)

        buttonLayout.addWidget(self.startBtn)
        buttonLayout.addWidget(self.stopBtn)

        self.vBoxLayout.addWidget(self.statusLabel)
        self.vBoxLayout.addWidget(self.progressBar)
        self.vBoxLayout.addLayout(buttonLayout)

        self.vBoxLayout.addStretch(1)

        # ==================================================
        # 3. 底部导航
        # ==================================================
        navLayout = QHBoxLayout()
        self.prevBtn = PushButton("上一步", self.scrollWidget)
        self.prevBtn.clicked.connect(self.prevClicked.emit)

        navLayout.addWidget(self.prevBtn)
        navLayout.addStretch(1)

        self.vBoxLayout.addLayout(navLayout)

    # --------------------------------------------------
    # 逻辑部分
    # --------------------------------------------------
    def select_output_dir(self):
        """选择输出目录"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择最终输出目录", self.config.output_dir)
        if dir_path:
            self.config.output_dir = dir_path
            self.outputDirCard.setContent(f"当前: {os.path.abspath(dir_path)}")

    def start_processing(self):
        """启动 AI 任务"""
        if not self.config.input_video_path or not os.path.exists(self.config.input_video_path):
            self._msg("提示", "未检测到有效的视频文件，请返回步骤 1 选择。", True)
            return

        # 切换按钮状态
        self.startBtn.setEnabled(False)
        self.startBtn.setText("处理中...")
        self.stopBtn.setEnabled(True)

        # 初始化 Worker
        self.worker = AIWorker(self.config)

        # 绑定信号
        self.worker.progress_signal.connect(lambda v, t: (self.progressBar.setValue(v), self.statusLabel.setText(t)))

        # 1. 正常完成的信号 (显示成功消息)
        self.worker.finished_signal.connect(lambda: self._msg("完成", "处理结束", False))

        # 2. 错误的信号
        self.worker.error_signal.connect(lambda e: (self.statusLabel.setText("错误"), self._msg("失败", e, True)))

        # 3. 线程结束信号 (无论是完成、停止还是报错，都会触发，用于重置 UI)
        self.worker.finished.connect(self._on_worker_finished)

        self.worker.start()

    def stop_processing(self):
        """用户点击停止按钮"""
        if self.worker and self.worker.isRunning():
            self.statusLabel.setText("正在中止任务，请稍候...")
            self.stopBtn.setEnabled(False)
            self.worker.stop()

    def _on_worker_finished(self):
        """
        线程结束后的清理工作，并发送重置信号。
        """
        self.startBtn.setEnabled(True)
        self.startBtn.setText("开始生成处理")
        self.stopBtn.setEnabled(False)

        # 检查是否是用户手动停止
        if "中止" in self.statusLabel.text():
            self.statusLabel.setText("任务已中止")
            self.progressBar.setValue(0)
        elif self.progressBar.value() == 100:
            self.statusLabel.setText("处理完成")

        # 任务完成后，发送信号通知返回欢迎页
        self.resetWorkflow.emit()

    def _msg(self, title, content, is_error):
        func = InfoBar.error if is_error else InfoBar.success
        func(title=title, content=content, parent=self, position=InfoBarPosition.TOP, duration=3000)