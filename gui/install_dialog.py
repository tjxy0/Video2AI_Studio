from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QVBoxLayout, QLabel
from qfluentwidgets import MessageBoxBase, SubtitleLabel, ProgressBar, TextEdit

from core.dependency_installer import DependencyInstaller


class InstallDialog(MessageBoxBase):
    """
    依赖安装进度对话框
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel("正在初始化 AI 环境", self)
        self.viewLayout.addWidget(self.titleLabel)

        # 提示文本
        self.statusLabel = QLabel("正在下载并安装 PyTorch (CUDA) 和 xFormers...\n这可能需要几分钟，请勿关闭程序。", self)
        self.statusLabel.setWordWrap(True)
        self.viewLayout.addWidget(self.statusLabel)

        # 进度条 (不确定模式，因为 pip 进度难以精确解析)
        self.progressBar = ProgressBar(self)
        self.progressBar.setRange(0, 0)  # 开启繁忙动画
        self.viewLayout.addWidget(self.progressBar)

        # 日志窗口
        self.logEdit = TextEdit(self)
        self.logEdit.setPlaceholderText("安装日志将显示在这里...")
        self.logEdit.setReadOnly(True)
        self.logEdit.setFixedHeight(200)
        self.viewLayout.addWidget(self.logEdit)

        # 隐藏默认按钮，防止用户中途取消导致环境损坏
        self.yesButton.setVisible(False)
        self.cancelButton.setText("后台运行")
        self.cancelButton.setDisabled(True)  # 暂时禁用取消

        # 初始化安装器
        self.installer = DependencyInstaller()
        self.installer.log_signal.connect(self.append_log)
        self.installer.finished_signal.connect(self.on_finished)

        # 窗口显示后立即开始
        self.installer.start()

    def append_log(self, text):
        self.logEdit.append(text)
        # 自动滚动到底部
        self.logEdit.verticalScrollBar().setValue(
            self.logEdit.verticalScrollBar().maximum()
        )

    def on_finished(self, success):
        self.progressBar.setRange(0, 100)
        if success:
            self.progressBar.setValue(100)
            self.statusLabel.setText("安装完成！请重启软件以生效。")
            self.yesButton.setText("立即重启")
            self.yesButton.setVisible(True)
            self.yesButton.clicked.connect(self.accept)
        else:
            self.progressBar.setValue(0)
            self.statusLabel.setText("安装失败。请检查网络或查看日志。")
            self.cancelButton.setText("关闭")
            self.cancelButton.setEnabled(True)