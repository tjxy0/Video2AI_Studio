import subprocess
import webbrowser
import sys


class EnvironmentChecker:
    """
    负责检测 CUDA、FFmpeg、xFormers 状态，并提供修复引导
    """

    @staticmethod
    def check_ffmpeg():
        """检测系统路径中是否有 FFmpeg"""
        try:
            subprocess.run(
                ["ffmpeg", "-version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
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
            return False

    @staticmethod
    def check_xformers():
        """检测 xformers 库是否安装"""
        try:
            import xformers
            return True
        except (ImportError, OSError):
            return False

    @staticmethod
    def get_cuda_info():
        """获取显卡名称和显存大小"""
        try:
            import torch
            if torch.cuda.is_available():
                props = torch.cuda.get_device_properties(0)
                vram_gb = props.total_memory / (1024 ** 3)
                return f"{torch.cuda.get_device_name(0)} ({vram_gb:.1f} GB VRAM)"
        except (ImportError, OSError):
            pass
        return "N/A"

    @staticmethod
    def open_install_guide(tool_name):
        """交互式修复指引"""
        urls = {
            "ffmpeg": "https://ffmpeg.org/download.html",
            "pytorch": "https://pytorch.org/get-started/locally/",
            "xformers": "https://github.com/facebookresearch/xformers#installing-xformers"
        }
        webbrowser.open(urls.get(tool_name, "https://www.google.com"))