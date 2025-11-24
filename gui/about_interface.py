from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from qfluentwidgets import SubtitleLabel, ScrollArea, BodyLabel, HyperlinkButton, FluentIcon as FIF


class AboutInterface(ScrollArea):
    """
    关于页面 (About Interface)
    """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.scrollWidget = QWidget()
        self.vBoxLayout = QVBoxLayout(self.scrollWidget)
        self.setObjectName("aboutInterface")

        self._init_ui()

        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)

    def _init_ui(self):
        self.vBoxLayout.setContentsMargins(30, 20, 30, 30)
        self.vBoxLayout.setSpacing(15)

        # 标题
        self.vBoxLayout.addWidget(SubtitleLabel("关于 Video2AI Studio", self.scrollWidget))

        # 版本信息
        version_label = BodyLabel("版本: v0.1.0 (Beta)", self.scrollWidget)
        self.vBoxLayout.addWidget(version_label)

        # 简介
        intro_text = (
            "Video2AI Studio 是一个基于 Stable Diffusion 和 ControlNet 技术的视频风格化工作台。旨在帮助用户将普通视频一键转换为动漫、油画或各种艺术风格的视频。"
            "<br/><br/>"
            "该应用通过高效的帧处理、骨骼提取（OpenPose）和内存优化，确保在本地 GPU 上提供稳定且高质量的生成体验。"
            "<br/><br/>"
            "<s>主要是懒得一帧一帧手动处理了，干脆自动化</s>"
        )
        intro_label = BodyLabel(intro_text, self.scrollWidget)
        intro_label.setWordWrap(True)
        self.vBoxLayout.addWidget(intro_label)

        self.vBoxLayout.addSpacing(10)

        # 核心技术
        self.vBoxLayout.addWidget(SubtitleLabel("核心技术栈", self.scrollWidget))

        tech_stack = [
            "AI 框架: PyTorch",
            "推理库: Diffusers, Accelerate",
            "UI 框架: PyQt6, PyQt-Fluent-Widgets (Windows 11 Fluent Design)",
            "视频处理: FFmpeg, OpenCV"
        ]

        for item in tech_stack:
            tech_label = BodyLabel(f"• {item}", self.scrollWidget)
            self.vBoxLayout.addWidget(tech_label)

        self.vBoxLayout.addSpacing(10)

        # 链接
        self.vBoxLayout.addWidget(SubtitleLabel("项目链接", self.scrollWidget))

        github_link = HyperlinkButton(
            url='https://github.com/tjxy0/Video2AI_Studio',
            text='项目 GitHub ',
            icon=FIF.GITHUB,
            parent=self.scrollWidget
        )
        self.vBoxLayout.addWidget(github_link)

        document_link = HyperlinkButton(
            url='https://docs.example.com',
            text='用户文档',
            icon=FIF.DOCUMENT,
            parent=self.scrollWidget
        )
        self.vBoxLayout.addWidget(document_link)

        self.vBoxLayout.addStretch(1)