from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QListWidget, QListWidgetItem
)
from qfluentwidgets import (
    SubtitleLabel, FluentIcon as FIF, CardWidget, InfoBar, InfoBarPosition
)

# 导入所有步骤和欢迎页
from gui.welcome_interface import WelcomeInterface
from gui.home_interface import Step1Interface
from gui.step2_gen_params import Step2Interface
from gui.step3_control_output import Step3Interface
from core.config import GenerationConfig


class WorkflowInterface(QWidget):
    """
    流程管理容器: 负责集成所有步骤，并管理它们之间的导航
    """

    def __init__(self, config: GenerationConfig, parent=None):
        super().__init__(parent=parent)
        self.config = config
        self.vBoxLayout = QVBoxLayout(self)
        self.setObjectName("workflowInterface")

        # 页面栈和步骤列表
        self.stackWidget = QStackedWidget(self)
        self.stepList = QListWidget(self)

        self._init_interfaces()
        self._init_ui()
        self._init_navigation()

        # 初始进入欢迎页
        self.current_index = 0
        self.stackWidget.setCurrentIndex(self.current_index)
        self._update_step_list_selection()

    def _init_interfaces(self):
        """初始化所有步骤界面"""
        self.welcomeInterface = WelcomeInterface(self)
        self.step1Interface = Step1Interface(self.config, self)
        self.step2Interface = Step2Interface(self.config, self)
        self.step3Interface = Step3Interface(self.config, self)

        # 将所有界面添加到堆叠部件中 (顺序即为步骤顺序)
        self.stackWidget.addWidget(self.welcomeInterface)  # Index 0
        self.stackWidget.addWidget(self.step1Interface)  # Index 1
        self.stackWidget.addWidget(self.step2Interface)  # Index 2
        self.stackWidget.addWidget(self.step3Interface)  # Index 3

    def _init_ui(self):
        """设置整体布局"""
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)

        # 侧边导航栏 (简化版)
        self.stepList.setFixedWidth(250)
        self.stepList.setSpacing(5)
        self.stepList.setStyleSheet("""
            QListWidget {
                border: none; 
                background-color: transparent;
                padding: 10px 0;
            }
            QListWidget::item {
                height: 40px;
                padding-left: 15px;
            }
            QListWidget::item:selected {
                color: #0078D4; 
                background-color: #E6E6E6;
                border-left: 4px solid #0078D4;
            }
        """)

        # 步骤名称
        steps = ["欢迎", "1. 预处理", "2. 生成参数", "3. 任务控制"]
        for step_name in steps:
            item = QListWidgetItem(step_name, self.stepList)
            self.stepList.addItem(item)

        # 主布局：导航列表 + 堆叠页面
        hLayout = QHBoxLayout()
        hLayout.addWidget(self.stepList)
        hLayout.addWidget(self.stackWidget)
        self.vBoxLayout.addLayout(hLayout)

    def _init_navigation(self):
        """连接所有步骤间的信号"""

        # Welcome -> Step 1
        self.welcomeInterface.startClicked.connect(lambda: self._set_current_index(1))

        # Step 1 -> Step 2
        self.step1Interface.nextClicked.connect(lambda: self._set_current_index(2))

        # Step 2 <-> Step 3
        self.step2Interface.prevClicked.connect(lambda: self._set_current_index(1))
        self.step2Interface.nextClicked.connect(lambda: self._set_current_index(3))

        # Step 3 -> Step 2
        self.step3Interface.prevClicked.connect(lambda: self._set_current_index(2))

        # ===== 新增连接：任务结束后返回欢迎页 =====
        self.step3Interface.resetWorkflow.connect(lambda: self._set_current_index(0))
        # =======================================

        # 此外，监听 Step1 的 Pose Switch 变化，同步到 Step2
        self.step1Interface.poseSwitch.checkedChanged.connect(self._sync_pose_switch)

        # 禁用列表导航，强制用户使用按钮
        self.stepList.itemClicked.connect(self._disable_list_click)

    def _disable_list_click(self):
        """防止用户通过点击列表项跳跃步骤"""
        InfoBar.warning(
            '提示',
            '请使用页面底部的“上一步/下一步”按钮进行导航。',
            parent=self,
            duration=2000,
            position=InfoBarPosition.TOP_RIGHT
        )
        self._update_step_list_selection()  # 恢复正确的选择状态

    def _set_current_index(self, index):
        """设置当前堆栈索引，并更新列表选中状态"""
        if index == 2:
            # 进入步骤 2 时，同步一次 Pose 状态
            self._sync_pose_switch(self.config.enable_pose)

        self.current_index = index
        self.stackWidget.setCurrentIndex(index)
        self._update_step_list_selection()

    def _update_step_list_selection(self):
        """根据当前索引更新列表选中项"""
        # 保证选中状态和实际页面一致
        self.stepList.setCurrentRow(self.current_index)

    def _sync_pose_switch(self, is_checked):
        """同步 Step1 的骨骼开关状态到 Step2 的重绘幅度卡可见性"""
        self.step2Interface._on_pose_switch_changed(is_checked)