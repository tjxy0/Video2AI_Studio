from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QLabel
from qfluentwidgets import SettingCard, SwitchButton, Slider

class SimpleRangeSettingCard(SettingCard):
    valueChanged = pyqtSignal(int)
    def __init__(self, value, max_value, icon, title, content=None, parent=None):
        super().__init__(icon, title, content, parent)
        self.slider = Slider(Qt.Orientation.Horizontal, self)
        self.slider.setRange(1, max_value)
        self.slider.setValue(value)
        self.slider.setFixedWidth(150)
        self.valueLabel = QLabel(str(value), self)
        self.valueLabel.setFixedWidth(40)
        self.valueLabel.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.hBoxLayout.addWidget(self.valueLabel, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(10)
        self.hBoxLayout.addWidget(self.slider, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)
        self.slider.valueChanged.connect(lambda v: (self.valueLabel.setText(str(v)), self.valueChanged.emit(v)))

    def setValue(self, value):
        self.slider.setValue(value)
        self.valueLabel.setText(str(value))

class SimpleSwitchSettingCard(SettingCard):
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
        self.switchButton.checkedChanged.connect(lambda v: (self.stateLabel.setText("开启" if v else "关闭"), self.checkedChanged.emit(v)))