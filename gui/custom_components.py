from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QLabel
from qfluentwidgets import (
    SettingCard, SwitchButton, SpinBox, DoubleSpinBox, LineEdit
)


class SimpleSpinBoxSettingCard(SettingCard):
    """
    [修改] 整数输入设置卡片 (替代滑块)
    """
    valueChanged = pyqtSignal(int)

    def __init__(self, value, min_value, max_value, icon, title, content=None, parent=None):
        super().__init__(icon, title, content, parent)

        self.spinBox = SpinBox(self)
        self.spinBox.setRange(min_value, max_value)
        self.spinBox.setValue(value)
        self.spinBox.setFixedWidth(200)

        self.hBoxLayout.addWidget(self.spinBox, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)

        self.spinBox.valueChanged.connect(self.valueChanged)

    def setValue(self, value):
        self.spinBox.setValue(value)


class SimpleDoubleSpinBoxSettingCard(SettingCard):
    """
    [新增] 浮点数输入设置卡片 (用于 CFG Scale 等)
    """
    valueChanged = pyqtSignal(float)

    def __init__(self, value, min_value, max_value, step, icon, title, content=None, parent=None):
        super().__init__(icon, title, content, parent)

        self.spinBox = DoubleSpinBox(self)
        self.spinBox.setRange(min_value, max_value)
        self.spinBox.setSingleStep(step)
        self.spinBox.setValue(value)
        self.spinBox.setFixedWidth(200)

        self.hBoxLayout.addWidget(self.spinBox, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)

        self.spinBox.valueChanged.connect(self.valueChanged)

    def setValue(self, value):
        self.spinBox.setValue(value)


class SimpleLineEditSettingCard(SettingCard):
    """
    [新增] 文本输入设置卡片 (用于 Seed 种子)
    """
    textChanged = pyqtSignal(str)

    def __init__(self, text, placeholder, icon, title, content=None, parent=None):
        super().__init__(icon, title, content, parent)

        self.lineEdit = LineEdit(self)
        self.lineEdit.setPlaceholderText(placeholder)
        self.lineEdit.setText(text)
        self.lineEdit.setFixedWidth(200)

        self.hBoxLayout.addWidget(self.lineEdit, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)

        self.lineEdit.textChanged.connect(self.textChanged)

    def setText(self, text):
        self.lineEdit.setText(text)


class SimpleSwitchSettingCard(SettingCard):
    """
    开关设置卡片 (保持不变)
    """
    checkedChanged = pyqtSignal(bool)

    def __init__(self, is_checked, icon, title, content=None, parent=None):
        super().__init__(icon, title, content, parent)

        self.switchButton = SwitchButton(self)
        self.switchButton.setChecked(is_checked)

        self.stateLabel = QLabel("开启" if is_checked else "关闭", self)
        self.stateLabel.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.hBoxLayout.addWidget(self.stateLabel, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(10)
        self.hBoxLayout.addWidget(self.switchButton, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)

        self.switchButton.checkedChanged.connect(self.__onCheckedChanged)

    def __onCheckedChanged(self, is_checked):
        self.stateLabel.setText("开启" if is_checked else "关闭")
        self.checkedChanged.emit(is_checked)