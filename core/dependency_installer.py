import sys
import subprocess
from PyQt6.QtCore import QThread, pyqtSignal

class DependencyInstaller(QThread):
    """
    后台安装线程：执行 pip install 命令并实时反馈日志
    """
    log_signal = pyqtSignal(str)      # 实时日志信号
    finished_signal = pyqtSignal(bool)# 安装完成信号 (True=成功, False=失败)

    def __init__(self):
        super().__init__()
        # 强制指定 CUDA 13.0 的源，确保安装的是 GPU 版本
        self.index_url = "https://download.pytorch.org/whl/cu128"
        self.packages = [
            "torch",
            "torchvision",
            "torchaudio",
            "xformers"
        ]

    def run(self):
        self.log_signal.emit(">>> 开始准备安装核心 AI 依赖库...")
        self.log_signal.emit(f">>> 目标源: {self.index_url}")
        self.log_signal.emit(f">>> 安装列表: {', '.join(self.packages)}")
        self.log_signal.emit(">>> 注意：文件较大，请保持网络畅通...\n")

        # 构建 pip 命令
        # 使用 sys.executable 确保安装到当前 Python 环境
        cmd = [
            sys.executable, "-m", "pip", "install",
            *self.packages,
            "--index-url", self.index_url,
            "--no-cache-dir" # 避免缓存占用过多空间
        ]

        try:
            # 启动子进程，通过管道捕获输出
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8', # 防止中文乱码
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )

            # 实时读取日志
            for line in process.stdout:
                self.log_signal.emit(line.strip())

            process.wait()

            if process.returncode == 0:
                self.log_signal.emit("\n>>> ✅ 安装成功！")
                self.finished_signal.emit(True)
            else:
                self.log_signal.emit(f"\n>>> ❌ 安装失败，返回码: {process.returncode}")
                self.finished_signal.emit(False)

        except Exception as e:
            self.log_signal.emit(f"\n>>> ❌ 发生严重错误: {str(e)}")
            self.finished_signal.emit(False)