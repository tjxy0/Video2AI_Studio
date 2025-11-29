import os
import shutil  # 新增导入：用于目录清理
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFileDialog
from qfluentwidgets import (
    SubtitleLabel, PrimaryPushButton, PushButton, ProgressBar,
    InfoBar, InfoBarPosition, BodyLabel, FluentIcon as FIF,
    ScrollArea, PushSettingCard, MessageBox, MessageBoxBase  # 新增 MessageBox 相关导入
)

from core.worker import AIWorker


class Step3Interface(ScrollArea):
    """
    工作流步骤 3: 输出设置与任务控制 (原 HomeInterface 的第 4/5 部分)
    """
    prevClicked = pyqtSignal()
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
        # 修改：连接到 _check_output_dir，以便执行预检查
        self.startBtn.clicked.connect(self._check_output_dir)

        self.stopBtn = PushButton("停止任务", self.scrollWidget)
        self.stopBtn.setEnabled(False)
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

    def _check_output_dir(self):
        """检查 frames_out 目录是否包含旧文件，并请求用户确认"""
        if not self.config.input_video_path or not os.path.exists(self.config.input_video_path):
            self._msg("提示", "未检测到有效的视频文件，请返回步骤 1 选择。", True)
            return

        out_dir = os.path.join(self.config.output_dir, "frames_out")

        # 检查 frames_out 目录是否存在且不为空
        if os.path.exists(out_dir) and len(os.listdir(out_dir)) > 0:

            # 使用自定义 MessageBox 进行确认
            w = MessageBox(
                "确认覆盖",
                f"在目录 '{out_dir}' 中检测到 {len(os.listdir(out_dir))} 个旧的帧文件。是否覆盖并继续生成？",
                self
            )
            w.yesButton.setText("覆盖并继续")
            w.cancelButton.setText("取消")

            # 默认按钮设为取消，避免误触
            w.setDefaultButton(MessageBoxBase.CancelButton)

            if w.exec():
                # 用户选择 '覆盖并继续' (Yes)
                self.start_processing()
            else:
                # 用户选择 '取消' (Cancel)
                self.statusLabel.setText("已取消任务")
        else:
            # 目录为空或不存在，直接开始
            self.start_processing()

    def _clear_frames_out(self):
        """清理 frames_out 文件夹"""
        out_dir = os.path.join(self.config.output_dir, "frames_out")
        if os.path.exists(out_dir):
            try:
                shutil.rmtree(out_dir)
                print(f"清理 frames_out 目录成功: {out_dir}")
            except Exception as e:
                print(f"清理 frames_out 目录失败: {e}")

    def select_output_dir(self):
        """选择输出目录"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择最终输出目录", self.config.output_dir)
        if dir_path:
            self.config.output_dir = dir_path
            self.outputDirCard.setContent(f"当前: {os.path.abspath(dir_path)}")

    def start_processing(self):
        """启动 AI 任务"""
        # 此时已通过 _check_output_dir 验证视频路径

        # 切换按钮状态
        self.startBtn.setEnabled(False)
        self.startBtn.setText("处理中...")
        self.stopBtn.setEnabled(True)

        # 初始化 Worker
        self.worker = AIWorker(self.config)

        # 绑定信号
        self.worker.progress_signal.connect(lambda v, t: (self.progressBar.setValue(v), self.statusLabel.setText(t)))

        # 1. 正常完成的信号 (显示成功消息)
        # 这里只触发消息提示，并在 finished 信号中处理重置和清理
        self.worker.finished_signal.connect(lambda: self._msg("完成", "视频生成处理完成！", False, duration=5000))

        # 2. 错误的信号
        self.worker.error_signal.connect(lambda e: (self.statusLabel.setText("错误"), self._msg("失败", e, True)))

        # 3. 线程结束信号 (无论是完成、停止还是报错，都会触发，用于重置 UI 和清理)
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
        is_success = self.progressBar.value() == 100

        self.startBtn.setEnabled(True)
        self.startBtn.setText("开始生成处理")
        self.stopBtn.setEnabled(False)

        if is_success:
            self.statusLabel.setText("处理完成")
        elif "中止" in self.statusLabel.text():
            self.statusLabel.setText("任务已中止")
            self.progressBar.setValue(0)

        # 任务完成后：

        # 1. 清理 frames_out 文件夹
        self._clear_frames_out()

        # 2. 发送信号通知返回欢迎页
        # 使用 QTimer 延迟重置，确保用户能看到 InfoBar 的提示（如果设置了 duration）
        QTimer.singleShot(5000, self.resetWorkflow.emit)  # 延迟 5 秒后发送重置信号

    def _msg(self, title, content, is_error, duration=3000):
        """统一的消息提示函数"""
        func = InfoBar.error if is_error else InfoBar.success
        func(title=title, content=content, parent=self, position=InfoBarPosition.TOP, duration=duration)