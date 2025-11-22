import subprocess
import torch
import webbrowser


class EnvironmentChecker:
    """
    对应报告 7.1 节：环境完整性保障
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
        """检测 CUDA 是否可用"""
        return torch.cuda.is_available()

    @staticmethod
    def get_cuda_info():
        """获取显卡名称，用于 GUI 显示"""
        if torch.cuda.is_available():
            return torch.cuda.get_device_name(0)
        return "N/A"

    @staticmethod
    def open_install_guide(tool_name):
        """对应报告 7.2：交互式修复指引"""
        urls = {
            "ffmpeg": "https://ffmpeg.org/download.html",
            "pytorch": "https://pytorch.org/get-started/locally/"
        }
        webbrowser.open(urls.get(tool_name, "https://www.google.com"))