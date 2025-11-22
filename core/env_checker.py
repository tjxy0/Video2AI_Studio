import subprocess
import webbrowser


class EnvironmentChecker:
    """
    负责检测 CUDA 和 FFmpeg 状态，并提供修复引导
    """

    @staticmethod
    def check_ffmpeg():
        """检测系统路径中是否有 FFmpeg"""
        try:
            subprocess.run(
                ["ffmpeg", "-version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            return True
        except FileNotFoundError:
            return False

    @staticmethod
    def check_cuda():
        """检测 CUDA 是否可用 (延迟加载 torch 以防止 DLL 错误导致崩溃)"""
        try:
            import torch
            return torch.cuda.is_available()
        except (ImportError, OSError):
            # 捕获 DLL 初始化失败或未安装的错误
            return False

    @staticmethod
    def get_cuda_info():
        """获取显卡名称，用于 GUI 显示"""
        try:
            import torch
            if torch.cuda.is_available():
                return torch.cuda.get_device_name(0)
        except (ImportError, OSError):
            pass
        return "N/A (或环境损坏)"

    @staticmethod
    def open_install_guide(tool_name):
        """交互式修复指引"""
        urls = {
            "ffmpeg": "https://ffmpeg.org/download.html",
            "pytorch": "https://pytorch.org/get-started/locally/"
        }
        webbrowser.open(urls.get(tool_name, "https://www.google.com"))